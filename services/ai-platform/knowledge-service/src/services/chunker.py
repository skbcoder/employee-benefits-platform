"""Semantic-aware document chunking for the RAG pipeline.

Splits documents on structural boundaries (headers, paragraphs, list groups)
rather than fixed word counts, preserving semantic coherence within each chunk.
"""

import re
from dataclasses import dataclass

from config.settings import settings


@dataclass
class Chunk:
    index: int
    content: str
    token_count: int


# Approximate tokens from word count (1 word ~= 1.33 tokens)
_TOKEN_RATIO = 1.33


def _estimate_tokens(text: str) -> int:
    """Estimate token count from text using word-based approximation."""
    return int(len(text.split()) * _TOKEN_RATIO)


# ---------------------------------------------------------------------------
#  Step 1: Split on structural boundaries
# ---------------------------------------------------------------------------

# Matches markdown headers (# through ######) at the start of a line
_HEADER_RE = re.compile(r"^(#{1,6}\s+.+)$", re.MULTILINE)

# Split points: double newline (paragraph), horizontal rule, or before a header
_SECTION_SPLIT_RE = re.compile(r"\n{2,}|^-{3,}\s*$|^={3,}\s*$", re.MULTILINE)


def _split_into_sections(text: str) -> list[tuple[str | None, str]]:
    """Split document into (header, body) sections.

    Respects markdown headers, paragraph breaks, and horizontal rules.
    Each section carries the most recent header for context.
    """
    # First, split on double-newlines and horizontal rules
    raw_parts = _SECTION_SPLIT_RE.split(text)

    sections: list[tuple[str | None, str]] = []
    current_header: str | None = None

    for part in raw_parts:
        part = part.strip()
        if not part:
            continue

        # Check if this part starts with a markdown header
        header_match = _HEADER_RE.match(part)
        if header_match:
            # Extract the header line
            header_line = header_match.group(1).strip()
            # The rest of the part after the header (if any)
            rest = part[header_match.end():].strip()
            current_header = header_line
            if rest:
                sections.append((current_header, f"{current_header}\n\n{rest}"))
            else:
                # Header alone — will be merged with next section
                sections.append((current_header, current_header))
        else:
            # Regular content paragraph — attach current header context
            sections.append((current_header, part))

    return sections


# ---------------------------------------------------------------------------
#  Step 2: Merge small adjacent sections
# ---------------------------------------------------------------------------


def _top_level_header(header: str | None) -> str | None:
    """Extract the top-level heading text (## level) for grouping."""
    if not header:
        return None
    # Match ##-level headers (not ### sub-headers)
    m = re.match(r"^#{1,2}\s+(.+)", header)
    return m.group(1).strip() if m else None


def _merge_small_sections(
    sections: list[tuple[str | None, str]],
    min_tokens: int,
    max_tokens: int,
) -> list[tuple[str | None, str]]:
    """Merge adjacent sections that are too small to embed well.

    Only merges sections under the same top-level header to avoid
    combining unrelated topics (e.g., Medical Rules + Dental Benefits).
    """
    if not sections:
        return []

    merged: list[tuple[str | None, str]] = []
    current_header, current_text = sections[0]

    for header, text in sections[1:]:
        combined = f"{current_text}\n\n{text}"
        combined_tokens = _estimate_tokens(combined)
        same_topic = _top_level_header(header) == _top_level_header(current_header)

        if (
            _estimate_tokens(current_text) < min_tokens
            and combined_tokens <= max_tokens
            and (same_topic or header is None)
        ):
            # Merge — keep the more specific header (latest non-None)
            current_text = combined
            if header is not None:
                current_header = header
        else:
            # Emit current, start new accumulation
            merged.append((current_header, current_text))
            current_header = header
            current_text = text

    # Don't forget the last accumulated section
    merged.append((current_header, current_text))
    return merged


# ---------------------------------------------------------------------------
#  Step 3: Split oversized sections at sentence boundaries
# ---------------------------------------------------------------------------

# Sentence endings followed by space+uppercase, newline, or end of string
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\n])|(?<=\n)(?=\S)")


def _split_oversized(
    header: str | None,
    text: str,
    max_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """Split an oversized section at sentence boundaries.

    Prepends the section header to each sub-chunk for context.
    """
    if _estimate_tokens(text) <= max_tokens:
        return [text]

    # Split into sentences / lines
    sentences = _SENTENCE_END_RE.split(text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [text]

    # Determine the header prefix for sub-chunks
    # If the text already starts with the header, don't double it
    header_prefix = ""
    if header and not text.startswith(header):
        header_prefix = f"{header}\n\n"

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_tokens = _estimate_tokens(header_prefix)

    for sentence in sentences:
        sentence_tokens = _estimate_tokens(sentence)

        if current_tokens + sentence_tokens > max_tokens and current_sentences:
            # Emit current chunk
            chunk_text = header_prefix + " ".join(current_sentences)
            chunks.append(chunk_text.strip())

            # Overlap: keep the last few sentences for context continuity
            overlap_sents: list[str] = []
            overlap_tok = _estimate_tokens(header_prefix)
            for s in reversed(current_sentences):
                st = _estimate_tokens(s)
                if overlap_tok + st > overlap_tokens:
                    break
                overlap_sents.insert(0, s)
                overlap_tok += st

            current_sentences = overlap_sents
            current_tokens = overlap_tok

        current_sentences.append(sentence)
        current_tokens += sentence_tokens

    # Emit remaining
    if current_sentences:
        chunk_text = header_prefix + " ".join(current_sentences)
        chunks.append(chunk_text.strip())

    return chunks


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------


def chunk_document(text: str) -> list[Chunk]:
    """Split document text into semantically coherent chunks.

    Uses a three-phase approach:
    1. Split on structural boundaries (headers, paragraphs, horizontal rules)
    2. Merge small adjacent sections to avoid tiny chunks
    3. Split oversized sections at sentence boundaries, preserving headers

    Returns the same Chunk dataclass as the original chunker —
    downstream code (vector_store, embedder) is unaffected.
    """
    if not text or not text.strip():
        return []

    max_tokens = settings.chunk_size
    min_tokens = settings.min_chunk_size
    overlap_tokens = settings.chunk_overlap

    # Step 1: structural split
    sections = _split_into_sections(text)

    if not sections:
        return []

    # Step 2: merge small sections
    sections = _merge_small_sections(sections, min_tokens, max_tokens)

    # Step 3: split oversized sections, emit chunks
    chunks: list[Chunk] = []
    index = 0

    for header, section_text in sections:
        sub_chunks = _split_oversized(header, section_text, max_tokens, overlap_tokens)

        for sub in sub_chunks:
            token_count = _estimate_tokens(sub)
            chunks.append(Chunk(index=index, content=sub, token_count=token_count))
            index += 1

    return chunks
