import re

import httpx

from config.settings import settings
from src.datasets.loader import EvalTestCase, OrchestrateResponse
from src.evaluators.base import BaseEvaluator, EvalResult

RELEVANCE_PROMPT_TEMPLATE = """You are an evaluation judge. Rate the relevance of the following response to the user's question on a scale of 1-5.

1 = Completely irrelevant, does not address the question at all
2 = Mostly irrelevant, touches on the topic but misses the point
3 = Partially relevant, addresses some aspects but incomplete
4 = Mostly relevant, addresses the question with minor gaps
5 = Fully relevant, directly and completely addresses the question

User Question: {question}

Response: {response}

Expected Behavior: {expected_behavior}

Provide ONLY a single integer from 1 to 5 as your rating. Do not include any other text."""


class RelevanceEvaluator(BaseEvaluator):
    """Evaluates response relevance using LLM-as-judge with heuristic fallback."""

    name: str = "relevance"

    def __init__(self, orchestrator_url: str | None = None, timeout: int | None = None):
        self._orchestrator_url = orchestrator_url or settings.orchestrator_url
        self._timeout = timeout or settings.eval_timeout_seconds

    async def evaluate(
        self, test_case: TestCase, response: OrchestrateResponse
    ) -> EvalResult:
        # Try LLM-as-judge first
        score = await self._llm_judge(test_case, response)
        method = "llm-as-judge"

        # Fall back to heuristic if LLM unavailable
        if score is None:
            score = self._heuristic_score(test_case, response)
            method = "keyword-heuristic"

        passed = score >= 0.6

        return EvalResult(
            evaluator=self.name,
            test_case_id=test_case.id,
            passed=passed,
            score=score,
            details=f"Relevance score: {score:.2f} (method: {method})",
            metadata={"method": method, "raw_score": score},
        )

    async def _llm_judge(
        self, test_case: TestCase, response: OrchestrateResponse
    ) -> float | None:
        """Use the orchestrator to judge relevance. Returns 0.0-1.0 or None on failure."""
        prompt = RELEVANCE_PROMPT_TEMPLATE.format(
            question=test_case.input,
            response=response.response,
            expected_behavior=test_case.expected_behavior,
        )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                result = await client.post(
                    f"{self._orchestrator_url}/api/orchestrate",
                    json={
                        "message": prompt,
                        "conversation_id": "",
                        "history": [],
                    },
                )
                result.raise_for_status()
                data = result.json()
                text = data.get("response", "").strip()

                # Extract integer rating from response
                match = re.search(r"[1-5]", text)
                if match:
                    rating = int(match.group())
                    return (rating - 1) / 4.0  # Convert 1-5 to 0.0-1.0
                return None
        except (httpx.HTTPError, ValueError, KeyError):
            return None

    def _heuristic_score(
        self, test_case: TestCase, response: OrchestrateResponse
    ) -> float:
        """Keyword overlap heuristic as fallback when LLM is unavailable."""
        if not response.response:
            return 0.0

        # Extract meaningful keywords from expected behavior and input
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "need", "must", "to", "of",
            "in", "for", "on", "with", "at", "by", "from", "as", "into", "about",
            "that", "this", "it", "its", "and", "or", "but", "if", "not", "no",
            "all", "any", "each", "every", "some", "such", "than", "too", "very",
        }

        def extract_keywords(text: str) -> set[str]:
            words = re.findall(r"\b[a-z]+\b", text.lower())
            return {w for w in words if w not in stop_words and len(w) > 2}

        expected_keywords = extract_keywords(
            test_case.expected_behavior + " " + test_case.input
        )
        response_keywords = extract_keywords(response.response)

        if not expected_keywords:
            return 0.5  # Neutral if no keywords to compare

        overlap = expected_keywords & response_keywords
        score = len(overlap) / len(expected_keywords)

        return min(score, 1.0)
