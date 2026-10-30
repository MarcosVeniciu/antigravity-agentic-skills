# Security & OWASP Audit (`references/review-security.md`)

OWASP/ASVS standards. Template: [`../resources/audit-report-template.md`](../resources/audit-report-template.md).

## 1. Scanner & Taint Analysis CLI

| Tool | CLI / Method | Scope |
| :--- | :--- | :--- |
| **Sinks** | `python skills/review/scripts/scan_sinks.py <modified_files>` | Flags dangerous sinks (`eval`, `exec`, `subprocess`, raw SQL). |
| **Taint** | Trace Call Hierarchy (1–2 levels outside diff). | Traces untrusted inputs to sinks. |

## 2. Security Invariants (OWASP / ASVS)

| Area | Invariant |
| :--- | :--- |
| **Secrets** | Scan for keys/tokens. 0 CVEs. Scrub committed secrets. |
| **Auth** | Generic login errors; `HttpOnly`, `Secure` cookies; rotate session ID. |
| **Authz (IDOR)** | Enforce server-side user/tenant filters on queries by ID. |
| **Injection** | Parameterized SQL only. Prohibit `shell=True`. Canonicalize paths (`safe.is_relative_to(BASE)`). |
| **Concurrency** | Atomic transactions with row locks (`SELECT ... FOR UPDATE`) or optimistic tokens. |
| **Web & Crypto** | CSRF tokens; strict CORS. CSPRNG (`secrets`, `crypto.randomUUID()`). |
| **Privacy (PII)** | Mask PII (`***REDACTED***`). Strip CRLF from inputs. Fail-secure. |

## 3. Surgical Remediation Patterns (Mode B)

```python
# Mode B: subprocess array, parameterized SQL, canonical path
subprocess.run(["convert", filename, "out.pdf"], check=True)
cursor.execute("SELECT * FROM users WHERE email = :email", {"email": email})
safe = (BASE_DIR / user_input).resolve()
if not safe.is_relative_to(BASE_DIR): raise SecurityError("Path traversal")
```

## 4. Forensic Report (`02-auditorias/audit-security-[slug].md`)

| ID | File:Line | OWASP Category | Evidence / Tool | Severity | Status |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `SEC-01` | `routes.py:42` | Injection | `scan_sinks.py` (`shell=True`) | High | 🔴 Non-Compliant |
