#!/usr/bin/env python3
"""
scan_sinks.py - OWASP v2 Code Crawling & Dangerous Sinks Scanner

Polyglot static analysis scanner for detecting dangerous APIs, insecure deserialization,
command injection, weak PRNG, SQL string interpolation, and modern web vectors
across Python (.py), JavaScript/TypeScript (.js, .ts, .tsx, .jsx), and Dart/Flutter (.dart).
Part of the workflows-skill/review package.
"""

import sys
import os
import re
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class VulnerabilityRule:
    rule_id: str
    name: str
    severity: str  # HIGH, MEDIUM, LOW
    description: str
    pattern: re.Pattern
    extensions: Tuple[str, ...]
    recommendation: str


RULES: List[VulnerabilityRule] = [
    # 1. Insecure Code Execution & Dynamic Evaluation
    VulnerabilityRule(
        rule_id="SEC-EXEC-01",
        name="Dynamic Code Execution (eval / exec)",
        severity="HIGH",
        description="Dynamic execution of untrusted strings allows Arbitrary Code Execution (ACE).",
        pattern=re.compile(r'\b(eval|exec|new\s+Function)\s*\(', re.IGNORECASE),
        extensions=(".py", ".js", ".ts", ".jsx", ".tsx"),
        recommendation="Replace dynamic evaluation with static data mapping or typed parsing."
    ),

    # 2. OS Command Injection
    VulnerabilityRule(
        rule_id="SEC-CMD-01",
        name="OS Command Injection (shell=True / exec)",
        severity="HIGH",
        description="Executing shell commands with shell=True or string concatenation enables OS command injection.",
        pattern=re.compile(
            r'(\bsubprocess\.(?:Popen|run|call|check_call|check_output)\s*\([^)]*shell\s*=\s*True|'
            r'\bos\.system\s*\(|'
            r'\bos\.popen\s*\(|'
            r'\bchild_process\.(?:exec|execSync)\s*\(|'
            r'\bProcess\.run\s*\([^)]*runInShell\s*:\s*true)',
            re.IGNORECASE | re.DOTALL
        ),
        extensions=(".py", ".js", ".ts", ".jsx", ".tsx", ".dart"),
        recommendation="Use argument lists without shell: subprocess.run(['cmd', arg], shell=False) or Process.run('cmd', [arg])."
    ),

    # 3. Insecure Deserialization
    VulnerabilityRule(
        rule_id="SEC-DESER-01",
        name="Insecure Deserialization (pickle / yaml unsafe)",
        severity="HIGH",
        description="Deserializing untrusted payloads via pickle or yaml.load leads to remote code execution.",
        pattern=re.compile(
            r'(\bpickle\.(?:loads?|Unpickler)|'
            r'\byaml\.load\s*\([^,\)]+\)|'
            r'\bmarshal\.loads?\b)',
            re.IGNORECASE
        ),
        extensions=(".py",),
        recommendation="Use safe serializers (json, msgpack) or yaml.safe_load(). Avoid pickle for untrusted input."
    ),

    # 4. SQL Injection via String Interpolation
    VulnerabilityRule(
        rule_id="SEC-SQL-01",
        name="SQL Injection (String Concatenation/Interpolation)",
        severity="HIGH",
        description="Embedding variables directly into SQL statements via f-strings or concatenation.",
        pattern=re.compile(
            r'(\bexecute\s*\(\s*f["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b|'
            r'\bexecute\s*\(\s*["\'].*(?:SELECT|INSERT|UPDATE|DELETE).*%s.*["\']\s*%)',
            re.IGNORECASE
        ),
        extensions=(".py", ".js", ".ts"),
        recommendation="Use parameterized queries: cursor.execute('SELECT * FROM t WHERE id = :id', {'id': val})."
    ),

    # 5. Weak PRNG in Security Contexts (CSPRNG vs Pseudo-Random)
    VulnerabilityRule(
        rule_id="SEC-PRNG-01",
        name="Weak PRNG for Security/Tokens",
        severity="HIGH",
        description="Standard PRNGs (random, Math.random) are predictable and must not generate tokens, keys, or IDs.",
        pattern=re.compile(
            r'(\b(?:token|secret|key|password|nonce|otp|salt|auth)\w*\s*=\s*.*(?:random\.(?:choice|random|randint|randrange)|Math\.random\s*\(\)))',
            re.IGNORECASE
        ),
        extensions=(".py", ".js", ".ts", ".jsx", ".tsx", ".dart"),
        recommendation="Use CSPRNG: 'import secrets' (Python), 'crypto.randomUUID()' / 'crypto.getRandomValues()' (JS/TS), or 'Random.secure()' (Dart)."
    ),

    # 6. DOM-Based XSS Sinks
    VulnerabilityRule(
        rule_id="SEC-XSS-01",
        name="DOM XSS Sink (innerHTML / dangerouslySetInnerHTML)",
        severity="HIGH",
        description="Writing unsanitized dynamic input to innerHTML or dangerouslySetInnerHTML causes XSS.",
        pattern=re.compile(r'(\.innerHTML\s*=|dangerouslySetInnerHTML\s*=)', re.IGNORECASE),
        extensions=(".js", ".ts", ".jsx", ".tsx"),
        recommendation="Use textContent, innerText, or sanitize via DOMPurify before injection."
    ),

    # 7. Permissive CORS with Wildcard and Credentials
    VulnerabilityRule(
        rule_id="SEC-CORS-01",
        name="Permissive CORS with Credentials",
        severity="HIGH",
        description="Allowing all origins (*) with credentials exposes sensitive authenticated sessions across origins.",
        pattern=re.compile(
            r'(allow_origins\s*=\s*\[?["\']\*["\']\]?[\s\S]*?allow_credentials\s*=\s*True|'
            r'Access-Control-Allow-Origin["\']?\s*:\s*["\']\*["\'][\s\S]*?credentials|'
            r'origin\s*:\s*["\']\*["\'][\s\S]{0,120}?credentials\s*:\s*true|'
            r'credentials\s*:\s*true[\s\S]{0,120}?origin\s*:\s*["\']\*["\'])',
            re.IGNORECASE
        ),
        extensions=(".py", ".js", ".ts"),
        recommendation="Specify explicit trusted domain origins instead of '*' when credentials/cookies are permitted."
    ),

    # 8. Hardcoded Secrets and Private Keys
    VulnerabilityRule(
        rule_id="SEC-SECRET-01",
        name="Hardcoded Secret / Token / Private Key",
        severity="HIGH",
        description="Hardcoded secrets in source code lead to credential compromise in repositories.",
        pattern=re.compile(
            r'(\b(?:api_key|secret_key|private_key|auth_token|jwt_secret|aws_secret_access_key)\s*=\s*["\'][A-Za-z0-9_\-\.\/]{16,}["\'])',
            re.IGNORECASE
        ),
        extensions=(".py", ".js", ".ts", ".jsx", ".tsx", ".dart"),
        recommendation="Move secrets to environment variables (os.getenv / process.env) or secret managers. If exposed, rotate and revoke immediately."
    ),

    # 9. Open Redirect / Unvalidated Destination
    VulnerabilityRule(
        rule_id="SEC-REDIR-01",
        name="Open Redirect (Unvalidated Destination)",
        severity="MEDIUM",
        description="Redirecting users to URLs derived directly from request query parameters without allowlist validation.",
        pattern=re.compile(
            r'(\b(?:redirect|HttpResponseRedirect)\s*\(\s*request\.(?:GET|query|params)\[?["\'](?:next|url|redirect|target)["\']\]?\s*\))',
            re.IGNORECASE
        ),
        extensions=(".py", ".js", ".ts"),
        recommendation="Validate destination URL against an explicit allowlist or restrict to relative paths starting with '/'."
    ),

    # 10. Path Traversal Sinks
    VulnerabilityRule(
        rule_id="SEC-PATH-01",
        name="Path Traversal Sink",
        severity="MEDIUM",
        description="Direct concatenation of user-controlled variables into file access paths.",
        pattern=re.compile(
            r'(\b(?:open|File)\s*\(\s*f["\'][^"\']*/\{|'
            r'\b(?:open|File)\s*\(\s*.*(?:path|dir|filename)\s*\+\s*request)',
            re.IGNORECASE
        ),
        extensions=(".py", ".js", ".ts", ".dart"),
        recommendation="Sanitize with os.path.basename() and verify canonical containment via Path.resolve().is_relative_to(base_dir)."
    )
]


@dataclass
class Finding:
    file_path: str
    line_number: int
    rule: VulnerabilityRule
    snippet: str


def scan_file(file_path: Path) -> Tuple[List[Finding], Optional[str]]:
    findings: List[Finding] = []
    ext = file_path.suffix.lower()
    
    applicable_rules = [r for r in RULES if ext in r.extensions]
    if not applicable_rules:
        return findings, None

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return findings, f"Failed to read {file_path}: {e}"

    for rule in applicable_rules:
        for match in rule.pattern.finditer(content):
            line_number = content[:match.start()].count('\n') + 1

            start_line_idx = content.rfind('\n', 0, match.start())
            start_line_idx = 0 if start_line_idx == -1 else start_line_idx + 1
            end_line_idx = content.find('\n', match.end())
            end_line_idx = len(content) if end_line_idx == -1 else end_line_idx

            raw_snippet = " ".join(content[start_line_idx:end_line_idx].split())
            
            # Mask sensitive values for SEC-SECRET-01 to prevent token leakage in reports
            if rule.rule_id == "SEC-SECRET-01":
                snippet = re.sub(r'(=[\s*]*["\'])([^"\']+)(["\'])', r'\1***REDACTED***\3', raw_snippet)
            else:
                snippet = raw_snippet

            findings.append(Finding(
                file_path=str(file_path),
                line_number=line_number,
                rule=rule,
                snippet=snippet
            ))
    return findings, None


def print_report(
    findings: List[Finding],
    files_scanned: int,
    files_with_errors: List[Tuple[str, str]],
    files_not_found: List[str]
) -> int:
    print(f"\n{'='*80}")
    print("🛡️  OWASP v2 CODE CRAWLING & DANGEROUS SINKS REPORT")
    print(f"{'='*80}")
    print(f"Total files eligible & scanned: {files_scanned}")
    print(f"Total findings: {len(findings)}")
    if files_with_errors:
        print(f"Files with read errors: {len(files_with_errors)}")
    if files_not_found:
        print(f"Targets not found: {len(files_not_found)}")
    print()

    if files_not_found:
        print("⚠️  MISSING TARGETS:")
        for nf in files_not_found:
            print(f"   [!] Target does not exist: {nf}")
        print()

    if files_with_errors:
        print("⚠️  FILE READ ERRORS:")
        for fp, err in files_with_errors:
            print(f"   [!] {fp}: {err}")
        print()

    if not findings and not files_with_errors and not files_not_found:
        print("✅ [PASS] No high or medium severity dangerous sinks detected in scanned files.")
        print(f"{'='*80}\n")
        return 0

    if not findings and (files_with_errors or files_not_found):
        print("⚠️ [INCOMPLETE] No dangerous sinks detected in readable files, but some targets could not be verified.")
        print(f"{'='*80}\n")
        return 1

    high_count = sum(1 for f in findings if f.rule.severity == "HIGH")
    med_count = sum(1 for f in findings if f.rule.severity == "MEDIUM")

    print(f"Severity Breakdown: 🔴 HIGH: {high_count} | 🟡 MEDIUM: {med_count}\n")
    print("-" * 80)

    for f in findings:
        icon = "🔴" if f.rule.severity == "HIGH" else "🟡"
        print(f"{icon} [{f.rule.severity}] {f.rule.rule_id} - {f.rule.name}")
        print(f"   📍 Location: {f.file_path}:{f.line_number}")
        print(f"   🔎 Snippet:  {f.snippet[:120]}")
        print(f"   ⚠️ Risk:     {f.rule.description}")
        print(f"   💡 Fix:      {f.rule.recommendation}")
        print("-" * 80)

    print(f"{'='*80}\n")
    has_blocking_issues = high_count > 0 or len(files_with_errors) > 0 or len(files_not_found) > 0
    return 1 if has_blocking_issues else 0


def main():
    parser = argparse.ArgumentParser(
        description="OWASP v2 Dangerous Sinks & Code Crawler for Antigravity Review Workflows"
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help="Files or directories to scan (supports .py, .js, .ts, .tsx, .dart)"
    )
    parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit with code 0 even if vulnerabilities or errors are found (for non-blocking runs)"
    )
    parser.add_argument(
        "--fail-on-medium",
        action="store_true",
        help="Exit with code 1 also when medium severity findings are present"
    )

    args = parser.parse_args()

    files_to_scan: List[Path] = []
    files_not_found: List[str] = []

    for target in args.targets:
        p = Path(target)
        if p.is_file():
            files_to_scan.append(p)
        elif p.is_dir():
            for ext in (".py", ".js", ".ts", ".tsx", ".jsx", ".dart"):
                files_to_scan.extend(p.glob(f"**/*{ext}"))
        else:
            files_not_found.append(target)

    all_findings: List[Finding] = []
    files_with_errors: List[Tuple[str, str]] = []

    for f in files_to_scan:
        findings, error = scan_file(f)
        if error:
            files_with_errors.append((str(f), error))
        all_findings.extend(findings)

    exit_code = print_report(all_findings, len(files_to_scan), files_with_errors, files_not_found)
    
    if args.fail_on_medium and any(f.rule.severity == "MEDIUM" for f in all_findings):
        exit_code = 1

    if args.exit_zero:
        sys.exit(0)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
