# Operational Guide: Security & OWASP Audit (Code Review Guide v2 & ASVS)

This guide governs the surgical audit and remediation of security vulnerabilities, injection flaws, taint analysis, secret management, SCA, LGPD/GDPR logging, race conditions, and modern web attack vectors.

---

## Phase 0 — Automated Code Crawling (Priority Guide)

Run the automated sink scanner against modified files to rapidly identify high-risk patterns:
```bash
python workflows-skill/review/scripts/scan_sinks.py <modified_files>
```

### Evaluation Protocol:
- Prioritize inspection on lines flagged by the scanner.
- **Taint Analysis & Call Hierarchy:** Trace untrusted input from external entry points (HTTP controllers, CLI arguments, gRPC handlers) to dangerous sinks across **1 to 2 levels up (caller) and 1 to 2 levels down (callee)** outside the diff.
- Verify whether authentication, role-based authorization, and strict sanitization were applied upstream.
- **Critical:** The scanner detects lexical patterns. Business logic flaws (BPOA, missing state transitions, logical bypasses) require semantic inspection across the entire diff.

---

## Phase 1 — In-Depth Code Inspection (Evidence Gathering)

### 1. Gestão de Segredos & SCA
- **Credenciais Expostas:** Scan the diff for hardcoded private keys, passwords, API tokens, or JWT secrets.
- **Ação em Caso de Vazamento:** A secret committed to git history is considered **permanently compromised**. Moving it to an environment variable is insufficient: mandate immediate revocation, rotation, and git history scrubbing.
- **SCA & Dependencies:** Verify whether newly added dependencies in `pyproject.toml` or `package.json` introduce known CVEs.

### 2. Autenticação & Gestão de Sessão
- **Enumeração de Usuários:** Ensure authentication failure messages are generic (`"Invalid credentials"`), preventing account enumeration.
- **Flags de Cookies de Sessão:** Verify sensitive cookies enforce `HttpOnly`, `Secure`, and `SameSite=Lax` or `SameSite=Strict`.
- **Session Fixation:** Ensure session IDs regenerate upon privilege level changes and invalidate cleanly on logout.

### 3. Autorização & Controle de Acesso (BPOA / IDOR)
- **Validação de Posse (Ownership):** Ensure that any operation accessing an entity by ID (`/api/orders/{id}`) validates server-side that the entity belongs to the authenticated user:
  ```python
  # Safe: server enforces ownership
  query = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id)
  ```
- **Missing Authorization:** Flag sensitive management endpoints lacking explicit permission/role decorators.

### 4. Injeção (SQL, NoSQL, Comandos do SO, Path Traversal)
- **SQL / NoSQL Injection:** Flag string concatenation or f-strings inside database queries. Require parameterized queries or ORM expression builders.
- **OS Command Injection:** Flag calls to `subprocess.run`, `subprocess.Popen`, `os.system`, or `child_process.exec` using `shell=True` or unescaped string arguments.
- **Path Traversal:** Flag user-controlled input interpolated into file paths. Enforce canonical path validation:
  ```python
  safe_path = (BASE_DIR / user_input).resolve()
  if not safe_path.is_relative_to(BASE_DIR):
      raise SecurityError("Path traversal detected")
  ```

### 5. Race Conditions & Concorrência (TOCTOU)
- **Check-Then-Act Flaws:** Flag balances, quotas, or coupon validations evaluated outside an atomic transaction.
- **Concorrência Segura:** Enforce row-level locks (`SELECT ... FOR UPDATE`), atomic database increments, or optimistic concurrency tokens (`version_id`).

### 6. Vetores Web Modernos: CSRF, CORS & Open Redirects
- **CSRF:** Ensure state-changing requests (POST, PUT, DELETE) require anti-CSRF tokens or `SameSite=Strict` cookies.
- **CORS:** Reject configurations pairing wildcard origins (`Access-Control-Allow-Origin: *`) with credentials (`Access-Control-Allow-Credentials: true`).
- **Open Redirects:** Validate target URLs against a strict allowlist of domain names or restrict to safe relative paths starting with `/` (rejecting `//evil.com` and `javascript:`).

### 7. Criptografia & Entropia (CSPRNG)
- **Geração de Tokens:** Sensitive tokens (reset tokens, API keys, session IDs) must use cryptographically secure generators (`secrets` in Python, `crypto.randomUUID()` in JS/TS, `Random.secure()` in Dart).
- Standard pseudo-random generators (`random.random()`, `Math.random()`) are strictly forbidden in security contexts.

### 8. Proteção de Dados, Privacidade (LGPD/GDPR) & Log Injection
- **Mascaramento de PII:** Passwords, tokens, credit card numbers, and government IDs must NEVER be written to application logs.
- **Log Injection (CRLF):** Strip carriage returns (`\r`) and newlines (`\n`) from untrusted inputs before logging to prevent log forging.
- **Fail-Secure Defaults:** Return generic client error payloads without leaking internal stack traces or database schema details.

---

## Phase 2 — Surgical Application & Mitigations (Mode B Only)

- **Safe OS Command Execution:**
  ```python
  # Before: vulnerable to command injection
  subprocess.run(f"convert {filename} output.pdf", shell=True)
  
  # After: safe argument vector without shell
  subprocess.run(["convert", filename, "output.pdf"], shell=False, check=True)
  ```
- **Parameterized Queries:**
  ```python
  # Before: SQL injection vulnerability
  cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
  
  # After: parameterized query
  cursor.execute("SELECT * FROM users WHERE email = :email", {"email": email})
  ```
- **Secret Sanitization:** Replace committed raw tokens with environment variable lookups (`os.environ["API_KEY"]`) and immediately record credential revocation ticket.

---

## Phase 3 — Audit Report Table Format

When recording findings for `02-auditorias/audit-security-[slug].md`, use this standardized schema:

```markdown
| ID | File / Line | OWASP / ASVS Category | Severity | Confidence | Disposition | Impact / Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SEC-01` | `src/api/routes.py:42` | Command Injection (A03:2021) | High | High | Confirmed | Subprocess invocation with shell=True and user-controlled path |
```
*(Always redact sensitive credentials in evidence: use `***REDACTED***`).*
