#!/usr/bin/env python3
"""
skills/ask/scripts/redact_sensitive_tokens.py
Deterministic Output Sanitizer & Inter-Agent Schema Validator for `/ask`.

Provides deterministic OWASP Top 10 for LLM & Agentic (2025/2026) mitigations:
1. redact_sensitive_tokens(text: str) -> str: [ASK-LLM02-01]
   Regex redaction of Bearer tokens, API keys (OpenAI, Anthropic, Google, Stripe,
   GitHub, AWS), database DSN credentials, private keys, and JWT tokens before
   rendering in chat or persisting to memory.
2. validate_research_json(output_str: str) -> tuple[bool, dict | None, list[str]]: [ASK-ASI07-01] / [ASK-ASI01-01]
   Strict JSON schema validation for the `research` subagent output.
   Enforces required fields (`status`, `files_scanned`, `evidence`, `summary`)
   and rejects free-form conversational text or prompt injection payloads.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REDACTED_TAG = "[REDACTED_SECRET]"

# Regex patterns for sensitive credentials & token redaction [ASK-LLM02-01]
SENSITIVE_PATTERNS: List[Tuple[str, re.Pattern]] = [
    # 1. Private Keys (RSA, EC, DSA, OpenSSH, etc.)
    (
        "PRIVATE_KEY",
        re.compile(
            r"-----BEGIN (?:[A-Z0-9_-]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z0-9_-]+ )?PRIVATE KEY-----"
        ),
    ),
    # 2. Bearer Tokens (HTTP Authorization Header format)
    (
        "BEARER_TOKEN",
        re.compile(r"(?i)\b(Bearer\s+)(?!tokens?\b)[A-Za-z0-9\-_~+/]+(?:\.[A-Za-z0-9\-_~+/]+)*={0,2}"),
    ),
    # 3. Database connection DSNs with embedded credentials (masking password only)
    (
        "DSN_PASSWORD",
        re.compile(
            r"((?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp|mariadb|cockroachdb|http|https)://[^:\s/@]*:)([^@\s]+)(@)"
        ),
    ),
    # 4. JSON Web Tokens (JWT) starting with 'eyJ'
    (
        "JWT_TOKEN",
        re.compile(r"\beyJ[A-Za-z0-9\-_=]{10,}\.[A-Za-z0-9\-_=]{10,}(?:\.[A-Za-z0-9\-_.+/=]+)?\b"),
    ),
    # 5. Anthropic API Keys (sk-ant-...)
    ("ANTHROPIC_KEY", re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{16,}\b")),
    # 6. OpenAI API Keys (sk-... or sk-proj-...)
    ("OPENAI_KEY", re.compile(r"\bsk-(?:proj-|admin-|none-)?[A-Za-z0-9\-_]{16,}\b")),
    # 7. Google Cloud / Gemini API Keys (AIza...)
    ("GOOGLE_KEY", re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b")),
    # 8. Stripe API Keys (sk_live_..., rk_live_..., sk_test_...)
    ("STRIPE_KEY", re.compile(r"\b(?:sk|rk)_(?:live|test)_[0-9a-zA-Z]{16,}\b")),
    # 9. GitHub Tokens (ghp_..., gho_..., ghu_..., ghs_..., ghr_..., github_pat_...)
    ("GITHUB_TOKEN", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    # 10. AWS Access Key IDs (AKIA..., ASIA...)
    ("AWS_ACCESS_KEY", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
]


def redact_sensitive_tokens(text: str) -> str:
    """
    Scans the input text and redacts credentials, API keys, DSN passwords, and tokens.
    Guarantees cross-platform sanitization before user-facing rendering [ASK-LLM02-01].
    """
    redacted = text
    for name, pattern in SENSITIVE_PATTERNS:
        if name == "BEARER_TOKEN":
            redacted = pattern.sub(rf"\g<1>{REDACTED_TAG}", redacted)
        elif name == "DSN_PASSWORD":
            redacted = pattern.sub(rf"\g<1>{REDACTED_TAG}\g<3>", redacted)
        else:
            redacted = pattern.sub(REDACTED_TAG, redacted)
    return redacted


VALID_STATUSES = {"SUCCESS", "NO_MATCH", "ERROR"}
ALLOWED_TOP_LEVEL_KEYS = {"status", "files_scanned", "evidence", "summary"}
ALLOWED_EVIDENCE_KEYS = {"path", "start_line", "end_line", "relevance", "snippet"}


def validate_research_json(output_str: str) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
    """
    Validates that the output of the `research` subagent strictly adheres to the JSON schema.

    Schema:
    {
      "status": "SUCCESS" | "NO_MATCH" | "ERROR",
      "files_scanned": ["<path>", ...],
      "evidence": [
        {
          "path": "<path>",
          "start_line": <int>,
          "end_line": <int>,
          "relevance": "<description>",
          "snippet": "<code>"
        }
      ],
      "summary": "<summary>"
    }

    Returns:
        (is_valid: bool, parsed_data: dict | None, errors: list[str])
    """
    errors: List[str] = []

    clean_str = output_str.strip()
    if clean_str.startswith("```"):
        lines = clean_str.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        clean_str = "\n".join(lines).strip()

    try:
        data = json.loads(clean_str, strict=False)
    except Exception as exc:
        return False, None, [f"JSON decoding failed: {exc}"]

    if not isinstance(data, dict):
        return False, None, [f"Root JSON element must be an object (dict), got {type(data).__name__}."]

    # Check for missing required fields
    for req_key in ("status", "files_scanned", "evidence", "summary"):
        if req_key not in data:
            errors.append(f"Missing required field: '{req_key}'.")

    # Check for unknown fields in root
    unknown_keys = set(data.keys()) - ALLOWED_TOP_LEVEL_KEYS
    if unknown_keys:
        errors.append(f"Unexpected field(s) in root object: {sorted(unknown_keys)}.")

    # Validate 'status'
    if "status" in data:
        status_val = data["status"]
        if not isinstance(status_val, str) or status_val not in VALID_STATUSES:
            errors.append(
                f"Field 'status' must be one of {sorted(VALID_STATUSES)}, got {repr(status_val)}."
            )

    # Validate 'files_scanned'
    if "files_scanned" in data:
        files_val = data["files_scanned"]
        if not isinstance(files_val, list):
            errors.append(f"Field 'files_scanned' must be a list of strings, got {type(files_val).__name__}.")
        else:
            for idx, item in enumerate(files_val):
                if not isinstance(item, str):
                    errors.append(
                        f"Field 'files_scanned[{idx}]' must be a string, got {type(item).__name__}."
                    )

    # Validate 'summary'
    if "summary" in data:
        summary_val = data["summary"]
        if not isinstance(summary_val, str):
            errors.append(f"Field 'summary' must be a string, got {type(summary_val).__name__}.")

    # Validate 'evidence'
    if "evidence" in data:
        evidence_val = data["evidence"]
        if not isinstance(evidence_val, list):
            errors.append(f"Field 'evidence' must be a list of objects, got {type(evidence_val).__name__}.")
        else:
            for idx, item in enumerate(evidence_val):
                if not isinstance(item, dict):
                    errors.append(
                        f"Field 'evidence[{idx}]' must be an object (dict), got {type(item).__name__}."
                    )
                    continue

                for ev_req in ("path", "start_line", "end_line", "relevance", "snippet"):
                    if ev_req not in item:
                        errors.append(f"Field 'evidence[{idx}].{ev_req}' is required.")

                unknown_ev_keys = set(item.keys()) - ALLOWED_EVIDENCE_KEYS
                if unknown_ev_keys:
                    errors.append(
                        f"Field 'evidence[{idx}]' has unexpected field(s): {sorted(unknown_ev_keys)}."
                    )

                if "path" in item and not isinstance(item["path"], str):
                    errors.append(
                        f"Field 'evidence[{idx}].path' must be a string, got {type(item['path']).__name__}."
                    )

                if "start_line" in item:
                    sl = item["start_line"]
                    if not isinstance(sl, int) or isinstance(sl, bool) or sl < 0:
                        errors.append(
                            f"Field 'evidence[{idx}].start_line' must be a non-negative integer, got {repr(sl)}."
                        )

                if "end_line" in item:
                    el = item["end_line"]
                    if not isinstance(el, int) or isinstance(el, bool) or el < 0:
                        errors.append(
                            f"Field 'evidence[{idx}].end_line' must be a non-negative integer, got {repr(el)}."
                        )
                    elif (
                        "start_line" in item
                        and isinstance(item["start_line"], int)
                        and not isinstance(item["start_line"], bool)
                        and el < item["start_line"]
                    ):
                        errors.append(
                            f"Field 'evidence[{idx}].end_line' ({el}) cannot be less than start_line ({item['start_line']})."
                        )

                if "relevance" in item and not isinstance(item["relevance"], str):
                    errors.append(
                        f"Field 'evidence[{idx}].relevance' must be a string, got {type(item['relevance']).__name__}."
                    )

                if "snippet" in item and not isinstance(item["snippet"], str):
                    errors.append(
                        f"Field 'evidence[{idx}].snippet' must be a string, got {type(item['snippet']).__name__}."
                    )

    is_valid = len(errors) == 0
    return is_valid, data if is_valid else (data if isinstance(data, dict) else None), errors


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic Output Sanitizer & Inter-Agent Schema Validator for `/ask`."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", metavar="TEXT", help="Redact sensitive tokens from inline string.")
    group.add_argument("--file", metavar="PATH", help="Redact sensitive tokens from a file.")
    group.add_argument("--stdin", action="store_true", help="Redact sensitive tokens from stdin.")
    group.add_argument(
        "--validate-json",
        metavar="JSON_OR_PATH",
        help="Validate research subagent JSON payload against strict schema (string or file path).",
    )

    args = parser.parse_args(argv)

    if args.text is not None:
        print(redact_sensitive_tokens(args.text))
        return 0

    if args.file is not None:
        path = Path(args.file)
        if not path.exists() or not path.is_file():
            print(f"[REDACT-ERROR] File not found: {args.file}", file=sys.stderr)
            return 1
        content = path.read_text(encoding="utf-8", errors="replace")
        print(redact_sensitive_tokens(content))
        return 0

    if args.stdin:
        content = sys.stdin.read()
        print(redact_sensitive_tokens(content))
        return 0

    if args.validate_json is not None:
        candidate_path = Path(args.validate_json)
        if candidate_path.exists() and candidate_path.is_file():
            raw_content = candidate_path.read_text(encoding="utf-8", errors="replace")
        else:
            raw_content = args.validate_json

        is_valid, parsed_data, errors = validate_research_json(raw_content)
        if not is_valid:
            print("[ASK-SCHEMA BLOCKED] Research subagent output failed schema validation:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 1

        print("[ASK-SCHEMA OK] Research subagent output strictly conforms to JSON schema.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
