# Skill: Auditoria de Segurança (`review-security`) - Alinhada ao OWASP v2

A skill **`review-security`** audita alterações de código sob uma perspectiva ofensiva e defensiva cirúrgica, alinhada às recomendações do **OWASP Code Review Guide v2**, **OWASP Top 10** e **ASVS**.

Operando sob a estratégia **Script-First**, a auditoria combina análise estática automatizada (*Code Crawling*) com inspeção manual pontual dos alertas gerados.

---

## 📚 Referência Externa Fundamental
* **Guia Base:** [`docs/references/OWASP_Code_Review_Guide_v2.pdf`](../references/OWASP_Code_Review_Guide_v2.pdf) (OWASP Code Review Guide 2.0).

---

## 📊 Matriz Comparativa: OWASP v2 vs Antigravity Skills

A tabela abaixo consolida a conformidade de ponta a ponta entre os 24 capítulos do guia oficial do OWASP e as capacidades de auditoria e testes do ecossistema:

| Capítulo OWASP v2 | Tema Central do Guia | Status | Onde foi Implementado / Mecanismo de Garantia |
| :--- | :--- | :---: | :--- |
| **Cap. 5 & 6** | Metodologia, S-SDLC, Triage & Scope | 🟢 **CONCLUÍDO** | [`workflows/review.md`](../../skills/review/SKILL.md) com permissão de **Call Hierarchy (Taint Analysis)** e estratégia **Script-First**. |
| **Cap. 6.11 & Apêndices** | **Code Crawling & Dangerous Sinks** | 🟢 **CONCLUÍDO** | Script nativo [`scan_sinks.py`](../../skills/review/scripts/scan_sinks.py) poliglota (Python, JS/TS, Dart) executando análise estática léxica e regex estruturada por chamadas inseguras e sinks perigosos. |
| **Cap. 7** | A1 - Injeções (SQL, NoSQL, OS Command) | 🟢 **CONCLUÍDO** | Detecção automatizada em [`scan_sinks.py`](../../skills/review/scripts/scan_sinks.py) (`SEC-CMD-01` e `SEC-SQL-01`) + [`checklist_security.md`](../../skills/review/references/review-security.md). |
| **Cap. 8** | A2 - Autenticação & Gestão de Sessão | 🟢 **CONCLUÍDO** | Checklist (Item 2) cobrindo regeneração de sessão pós-login (anti-session fixation), invalidação no logout e flags seguras (`HttpOnly`, `Secure`, `SameSite`). |
| **Cap. 9** | A3 - Cross-Site Scripting (XSS) & DOM XSS | 🟢 **CONCLUÍDO** | Detecção estática em [`scan_sinks.py`](../../skills/review/scripts/scan_sinks.py) (`SEC-XSS-01` para `innerHTML` e `dangerouslySetInnerHTML`) + codificação contextual. |
| **Cap. 10 & 13** | A4/A7 - IDOR & Quebra de Controle de Acesso | 🟢 **CONCLUÍDO** | Checklist (`user_id = current_user.id`) + **Padrão de teste unitário AAA de IDOR (403)** em [`aaa_mock_patterns.md`](../../skills/implement/references/tdd-test.md). |
| **Cap. 11** | A5 - Security Misconfiguration (CORS, Debug) | 🟢 **CONCLUÍDO** | Detecção estática em [`scan_sinks.py`](../../skills/review/scripts/scan_sinks.py) (`SEC-CORS-01` flagrando `*` com credenciais) + regras de hardening. |
| **Cap. 12** | A6 - Criptografia & Entropia (CSPRNG) | 🟢 **CONCLUÍDO** | Detecção estática em [`scan_sinks.py`](../../skills/review/scripts/scan_sinks.py) (`SEC-PRNG-01` proibindo `random`/`Math.random` em auth e exigindo `secrets`/`crypto`). |
| **Cap. 14** | **A8 - Cross-Site Request Forgery (CSRF)** | 🟢 **CONCLUÍDO** | Proteção em mutações no [`checklist_security.md`](../../skills/review/references/review-security.md) + **[STAGE 7]** no runner de [`test-integration`](../../skills/release/references/release-checklist.md). |
| **Cap. 15** | A9 - Componentes Vulneráveis (SCA) | 🟢 **CONCLUÍDO** | Checklist de auditoria de lockfiles e dependências com CVEs conhecidas. |
| **Cap. 16** | **A10 - Open Redirects & SSRF** | 🟢 **CONCLUÍDO** | Detecção estática em [`scan_sinks.py`](../../skills/review/scripts/scan_sinks.py) (`SEC-REDIR-01`) + **[STAGE 8]** no runner de [`test-integration`](../../skills/release/references/release-checklist.md). |
| **Cap. 17 & 18** | HTML5 (Storage/PostMessage) & CORS/SOP | 🟢 **CONCLUÍDO** | Coberto via `SEC-CORS-01` e `SEC-XSS-01` no [`scan_sinks.py`](../../skills/review/scripts/scan_sinks.py) + Item 6 do [`checklist_security.md`](../../skills/review/references/review-security.md). |
| **Cap. 19** | Logging & Log Injection (CRLF) | 🟢 **CONCLUÍDO** | Sanitização de `\r\n` no [`checklist_security.md`](../../skills/review/references/review-security.md) (Item 8) + teste unitário com `caplog` em [`aaa_mock_patterns.md`](../../skills/implement/references/tdd-test.md). |
| **Cap. 20** | Error Handling & Fail-Safe Defaults | 🟢 **CONCLUÍDO** | Princípio de *Fail Secure* no checklist + teste unitário de payload de erro sem vazamento de traceback em [`aaa_mock_patterns.md`](../../skills/implement/references/tdd-test.md). |
| **Cap. 21 & 22** | Alertas de Segurança & Defesa Ativa (AppSensor) | ⚪ **N/A (Runtime)** | Requisito de telemetria de produção (WAF / SIEM), fora do ciclo estático de código-fonte de desenvolvimento. |
| **Cap. 23** | **Race Conditions & Concorrência (TOCTOU)** | 🟢 **CONCLUÍDO** | Item 5 no [`checklist_security.md`](../../skills/review/references/review-security.md) (row locks / `SELECT FOR UPDATE`) + testes paralelos em [`aaa_mock_patterns.md`](../../skills/implement/references/tdd-test.md) + **[STAGE 9]** em [`test-integration`](../../skills/release/references/release-checklist.md). |
| **Cap. 24** | Gerenciamento de Memória & Buffer Overflows | ⚪ **N/A (Garbage Collection)** | Não aplicável a linguagens com gerenciamento automático de memória (Python, Node/TS, Dart). Aplicável estritamente a C/C++ puro. |

---

### ℹ️ Entendendo as Classificações "N/A"

1. **`N/A (Garbage Collection)` - Capítulo 24:**
   * **Conceito:** Buffer Overflows, Memory Leaks e corrupção de ponteiros ocorrem quando desenvolvedores manipulam memória física manualmente via `malloc` e `free` (em C/C++).
   * **Por que não se aplica:** Nossas linguagens de aplicação (**Python, TypeScript/JavaScript e Flutter/Dart**) são *memory-safe* e possuem **Garbage Collector (coletor automático de lixo)**. O runtime cuida da alocação de memória, tornando o transbordamento físico de buffer impossível no código de aplicação.
2. **`N/A (Runtime)` - Capítulos 21 e 22:**
   * **Conceito:** Detecção ativa de intrusões no nível da aplicação (*AppSensor*), honeypots e bloqueio automático de IPs sob ataque de força bruta.
   * **Por que não se aplica:** Essa proteção é implementada por ferramentas de **Produção / SecOps / Infraestrutura** (como WAF da Cloudflare/AWS, Datadog ou Elastic SIEM). O ciclo de review de código audita o código-fonte estático e os testes antes do deploy.

---

## 🛠️ Ferramenta de Code Crawling: `scan_sinks.py`

O script [`scan_sinks.py`](../../skills/review/scripts/scan_sinks.py) executa uma varredura sintática estática contra os arquivos da branch:

### Como Executar:
```bash
python skills/review-security/scripts/scan_sinks.py <arquivos_alterados>
```

### Regras Cobertas:
* `SEC-EXEC-01`: Execução dinâmica (`eval`, `exec`, `new Function`).
* `SEC-CMD-01`: Injeção de comandos de sistema operacional (`shell=True`, `child_process.exec`, `Process.run(runInShell: true)`).
* `SEC-DESER-01`: Desserialização insegura (`pickle.loads`, `yaml.load`).
* `SEC-SQL-01`: Injeção de SQL por interpolação de strings (`cursor.execute(f"...")`).
* `SEC-PRNG-01`: Geradores pseudo-aleatórios fracos em contextos sensíveis (`random.random()`, `Math.random()`).
* `SEC-XSS-01`: Sumidouros de DOM XSS (`innerHTML`, `dangerouslySetInnerHTML`).
* `SEC-CORS-01`: CORS com wildcard (`*`) e credenciais ativadas.
* `SEC-SECRET-01`: Chaves de API, senhas ou tokens privados hardcoded.
* `SEC-REDIR-01`: Redirecionamento aberto (*Open Redirect*) sem validação em lista de permissões.
* `SEC-PATH-01`: Concatenação direta em caminhos de arquivo (*Path Traversal*).

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/review-security/SKILL.md`](../../skills/review/SKILL.md)
* **Checklist Detalhado:** [`skills/review-security/references/checklist_security.md`](../../skills/review/references/review-security.md)
* **Script de Varredura:** [`skills/review-security/scripts/scan_sinks.py`](../../skills/review/scripts/scan_sinks.py)
* **Template de Relatório:** [`skills/review-security/resources/template_security.md`](../../skills/review/resources/audit-report-template.md)
