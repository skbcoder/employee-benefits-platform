#!/usr/bin/env python3
"""Seed the Knowledge Service with benefits documents.

Usage:
    python seed.py [--base-url http://localhost:8300]

This script reads all markdown documents from the seed-data directories
and ingests them into the Knowledge Service via its REST API.
"""

import argparse
import json
import sys
from pathlib import Path

import urllib.request
import urllib.error

SEED_DIR = Path(__file__).parent

# Document manifest: (category, directory, files with titles)
DOCUMENTS = [
    # Policy documents
    ("policy", "policy", [
        ("eligibility-rules.md", "Employee Benefits Eligibility Rules"),
        ("open-enrollment.md", "Open Enrollment Policy"),
        ("qualifying-life-events.md", "Qualifying Life Events Policy"),
        ("cobra-continuation.md", "COBRA Continuation Coverage Policy"),
    ]),
    # Plan documents
    ("plan", "plan", [
        ("medical-plans.md", "Medical Plan Options — Basic, Silver, Gold, Platinum"),
        ("dental-plans.md", "Dental Plan Options — Basic and Premium"),
        ("vision-plans.md", "Vision Plan Options — Basic and Premium"),
        ("life-insurance.md", "Life Insurance and AD&D Plans"),
    ]),
    # Compliance documents
    ("compliance", "compliance", [
        ("hipaa-privacy.md", "HIPAA Privacy and Security Compliance"),
        ("aca-compliance.md", "Affordable Care Act (ACA) Compliance"),
        ("erisa-requirements.md", "ERISA Compliance Requirements"),
        ("section125-cafeteria-plan.md", "Section 125 Cafeteria Plan"),
    ]),
    # FAQ documents
    ("faq", "faq", [
        ("enrollment-faq.md", "Benefits Enrollment FAQ"),
        ("claims-faq.md", "Claims and Coverage FAQ"),
    ]),
    # Process documents
    ("process", "process", [
        ("enrollment-processing-workflow.md", "Enrollment Processing Workflow"),
        ("benefits-administration-guide.md", "Benefits Administration Guide"),
    ]),
]


def ingest_document(base_url: str, title: str, content: str, category: str, source: str) -> dict:
    """Post a document to the Knowledge Service API."""
    url = f"{base_url}/api/knowledge/documents"
    payload = json.dumps({
        "title": title,
        "content": content,
        "category": category,
        "source": source,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def main():
    parser = argparse.ArgumentParser(description="Seed the Knowledge Service with benefits documents")
    parser.add_argument("--base-url", default="http://localhost:8300", help="Knowledge Service base URL")
    parser.add_argument("--dry-run", action="store_true", help="List documents without ingesting")
    args = parser.parse_args()

    total = sum(len(files) for _, _, files in DOCUMENTS)
    print(f"=== Seeding Knowledge Base ({total} documents) ===")
    print(f"Target: {args.base_url}")
    print()

    ingested = 0
    failed = 0

    for category, directory, files in DOCUMENTS:
        print(f"Category: {category}")
        for filename, title in files:
            filepath = SEED_DIR / directory / filename
            if not filepath.exists():
                print(f"  SKIP  {filename} (file not found)")
                failed += 1
                continue

            content = filepath.read_text(encoding="utf-8")
            source = f"seed-data/{directory}/{filename}"

            if args.dry_run:
                print(f"  DRY   {title} ({len(content)} chars)")
                ingested += 1
                continue

            try:
                result = ingest_document(args.base_url, title, content, category, source)
                chunk_count = result.get("chunk_count", "?")
                doc_id = result.get("document_id", "?")
                print(f"  OK    {title} -> {chunk_count} chunks (id: {doc_id[:8]}...)")
                ingested += 1
            except Exception as e:
                print(f"  FAIL  {title}: {e}")
                failed += 1

        print()

    print(f"=== Done: {ingested} ingested, {failed} failed ===")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
