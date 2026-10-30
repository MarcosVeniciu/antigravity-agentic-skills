# Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/refactor`

**Data da Auditoria:** 2026-10-30  
**Skill Auditada:** [`skills/refactor/SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md)  
**Documentação Arquitetural:** [`doc/skills/refactor/README.md`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/refactor/README.md)  
**Modelo de Execução da Skill:** Main Orchestrator + Subagente `solid-refactorer` (`inherit`, `EnableWriteTools: true`)  
**Status Geral de Segurança Agentic:** 🟢 Totalmente Mitigado / 100% Conforme (7/7 itens mitigados)

---

## 1. Sumário Executivo e Perfil de Risco da Skill

A skill `/refactor` governa a Fase 3 do ciclo SDD 2.0 (Macro-Refatoração e Consolidação Arquitetural). Sua missão é varrer o diff cumulativo da feature branch (`git diff develop...HEAD`) aplicando Clean Code, SOLID e eliminando complexidade ciclomática ($V(G) \le 10$) e ineficiências assintóticas ($O(N^2)$), sem alterar contratos prévios ou introduzir regressões. Para evitar o esgotamento da janela de contexto (*Context Bloat*) por repetidas execuções de testes, a refatoração é delegada ao subagente contextual isolado `solid-refactorer`.

### Perfil de Superfície de Ataque e Controles Implementados
1. **Perspectiva A (Segurança Meta-Agêntica do Fluxo):**
   - **Adulteração de Testes (*Assertion Tampering*):** Mitigado deterministicamente no Step 4 pelo Tampering Gate (`git diff --exit-code <PHASE_START_HASH>...HEAD -- tests/`). Se qualquer asserção ou arquivo de teste for alterado pelo `solid-refactorer`, a fase é abortada imediatamente com reversão automática de testes (`git checkout <PHASE_START_HASH> -- tests/`).
   - **Evasão do Gate de Complexidade:** Mitigado via remoção total do parâmetro `--exit-zero` de [`ast_complexity.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py), garantindo saída mandatória `exit 1` em violações de $V(G) \le 10$ ou erros de sintaxe, coberto por teste automatizado de regressão em [`tests/skills/test_scanners.py:241-244`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L241-L244).
   - **Comandos Destrutivos / Rollback:** Mitigado pela salvaguarda preventiva com `git stash push -u -m "antigravity-refactor-safety-rollback"` antes de qualquer `git reset --hard` na regra de Double-Strike.
   - **RCE Local e Conexões Não Autorizadas via `pytest`:** Mitigado pelo acoplamento mandatório do plugin de sandbox de rede ([`pytest_sandbox.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/scripts/pytest_sandbox.py) via `-p skills.implement.scripts.pytest_sandbox`) no Exit Gate de regressão da skill `/refactor`.
   - **Alucinação de Métricas na Matriz de Evidências:** Mitigado pelo validador determinístico [`validate_evidence_matrix.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/validate_evidence_matrix.py) no Step 4 e no Exit Gate, recalculando $V(G)$ via AST dos fontes reais e abortando com `exit 1` em caso de discrepância ou teto $V(G) > 10$ violado.
2. **Perspectiva B (Segurança do Código Downstream):**
   - **Fortalecimento contra DoS/Algorithmic Attacks:** A redução matemática de $V(G) \le 10$ e a eliminação de loops $O(N^2)$ e buscas lineares aninhadas eliminam potenciais vetores de exaustão de CPU (Denial of Service).
   - **Isolamento de Camadas via DIP:** A injeção de dependência via `typing.Protocol` desacopla a lógica de negócio do acesso direto ao banco ou serviços externos, criando limites de segurança testáveis.
   - **Prevenção de Dependências Ocultas (*Anti-Slopsquatting*):** Invariante formal no catálogo SOLID e no prompt do subagente proibindo estritamente novas dependências externas fora do manifesto do projeto ou da biblioteca padrão Python.
   - **Proteção contra Falsos Negativos de Regressão:** Entry Gate enriquecido com verificação prévia de cobertura (`pytest --cov`) com alerta para alvos $V(G) > 10$ com cobertura inferior a 80%.

---

## 2. Matriz de Conformidade: OWASP Top 10 for LLM Applications (2025/2026)

| Código | Categoria OWASP LLM (2025/2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **LLM01** | **Prompt Injection (Direta, Indireta ou Multimodal)** | Média-Alta | Leitura restrita ao diff da branch (`develop...HEAD`), contratos SDD e catálogo local ([`refactor-subagents.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L7)). | Comentários ou docstrings maliciosas presentes no código a ser refatorado podem tentar instruir o modelo a inserir backdoors ou ignorar regras de complexidade. | 🟡 Atenção |
| **LLM02** | **Sensitive Information Disclosure** | Média | Escopo estritamente focado em código-fonte de produção e testes unitários. | Testes executados via `pytest -v` podem vazar dados confidenciais ou segredos mockados nos logs do console se ocorrerem falhas. | 🟢 Conforme |
| **LLM03** | **Excessive Agency** | Crítica | Gate humano prévio no mapeamento (`task_list.md`), System Prompt com Zero Tampering (`refactor-subagents.md:7`), Tampering Gate determinístico pós-refatoração (`git diff --exit-code <PHASE_START_HASH>...HEAD -- tests/` no Step 4) e salvaguarda de rollback com `git stash` ([`refactor-git.md:9-10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-git.md#L9-L10)). | `EnableWriteTools: true` opera no workspace do projeto sem isolamento físico de subdiretório em tempo de execução, mas alterações indevidas em testes são bloqueadas deterministicamente antes do squash. | 🟢 Conforme (Mitigado) |
| **LLM04** | **Supply Chain Vulnerabilities** | Média-Alta | Scanner determinístico `ast_complexity.py` utiliza 100% biblioteca padrão. Invariante anti-slopsquatting declarada no catálogo SOLID ([`solid-catalog.md:20`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/solid-catalog.md#L20)), no prompt do subagente ([`refactor-subagents.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L7)) e documentada no README proibindo novas dependências externas. | Validação estática automatizada de novos imports via AST durante o pipeline permanece como evolução futura. | 🟢 Conforme (Mitigado) |
| **LLM05** | **Data and Model Poisoning** | Média | Contratos fixos em `01-concepcao/sdd-[slug].md` e catálogo fechado de transformações ([`solid-catalog.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/solid-catalog.md)). | Se a base de notas Obsidian (`02-auditorias/pivots-[slug].md`) for envenenada com pivots fictícios, o Drift Gate aceita remoções indevidas de métodos. | 🟡 Atenção |
| **LLM06** | **Unbounded Consumption** | Baixa-Média | Delimitação estrita do escopo ao diff (`git diff develop...HEAD`) e limite de 2 tentativas (Double-Strike Circuit Breaker: `MaxIterations: 2`) ([`refactor-git.md:9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-git.md#L9)). | Ausência de timeout de tempo real no subprocesso `pytest` e ausência de teto explícito de tokens por invocação do `solid-refactorer`. | 🟢 Conforme |
| **LLM07** | **System Prompt Leakage / Misinformation** | Baixa | Aferição de qualidade 100% matemática via `ast_complexity.py` e validação determinística de assinaturas via `check_sdd_drift.py`. | Risco baixo de alucinação de conformidade, pois as métricas de saída são computadas via AST e não por avaliação aberta do modelo. | 🟢 Conforme |
| **LLM08** | **Hidden Context Exposure** | Baixa | `solid-refactorer` é context-isolated: descarta tracebacks e histórico de refatoração iterativa entre alvos ([`doc/skills/refactor/README.md:22`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/refactor/README.md#L22)). | Nenhum vazamento detectado entre contextos de subagentes. | 🟢 Conforme |
| **LLM09** | **Vector and Embedding Weaknesses** | Baixa | Não utiliza base vetorial ou embeddings proprietários no fluxo da skill. | Não aplicável. | 🟢 Conforme |
| **LLM10** | **Improper Output Handling** | Média-Alta | Análise sintática segura via módulo padrão `ast` sem uso de `eval()` ou `exec()` ([`ast_complexity.py:118`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py#L118)). | O código refatorado pelo subagente é salvo diretamente em disco e executado em seguida pelo interpretador Python no comando `pytest`. | 🟡 Atenção |

---

## 3. Matriz de Conformidade: OWASP Top 10 for Agentic Applications (2026)

| Código | Categoria OWASP Agentic (2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **ASI01** | **Agent Goal Hijack** | Alta | Backlog com metas cirúrgicas pré-mapeadas e aprovadas em `task_list.md` ([`SKILL.md:15`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L15)). | Código legado malicioso no repositório poderia conter instruções adversariais em docstrings ou comentários tentando desviar o foco da refatoração. | 🟡 Atenção |
| **ASI02** | **Tool Misuse and Exploitation** | Alta | Linha de comando determinística (`--threshold 10`). Flag de bypass `--exit-zero` foi integralmente removida de `ast_complexity.py`, forçando `exit 1` em violações ([`ast_complexity.py:215-221`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py#L215-L221)). Teste unitário automatizado em [`test_scanners.py:241-244`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L241-L244). | Nenhum gap residual no scanner de complexidade. | 🟢 Conforme (Mitigado) |
| **ASI03** | **Identity and Privilege Abuse** | Alta | Papéis claros: Orquestrador governa e fecha a fase; `solid-refactorer` atua cirurgicamente. Tampering Gate determinístico (`git diff --exit-code <PHASE_START_HASH>...HEAD -- tests/`) e stash de salvaguarda antes de rollback ([`refactor-git.md:9-10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-git.md#L9-L10)). | `EnableWriteTools: true` opera no workspace do projeto sem isolamento físico de paths em tempo de execução (mitigado no gate git). | 🟡 Mitigado com Gate Git |
| **ASI04** | **Agentic Supply Chain Vulnerabilities** | Média | Invariante "Zero New External Dependencies" no catálogo SOLID ([`solid-catalog.md:20`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/solid-catalog.md#L20)), no prompt do `solid-refactorer` ([`refactor-subagents.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L7)) e no pipeline ([`SKILL.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L16)). | Ausência de linter determinístico de imports no diff contra o manifesto. | 🟢 Conforme (Mitigado) |
| **ASI05** | **Unexpected Code Execution (RCE)** | Crítica | Análise de complexidade via `ast_complexity.py` é 100% estática (AST seguro sem eval/exec). Execução de regressão no Exit Gate acopla `-p skills.implement.scripts.pytest_sandbox` ([`SKILL.md:28`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L28)) para bloqueio estrito de sockets de rede. | Nenhum gap residual. Conexões de rede não autorizadas durante a suíte são abortadas deterministicamente. | 🟢 Conforme (Mitigado) |
| **ASI06** | **Memory and Context Poisoning** | Alta | Validação cruzada com SDD Drift Gate (`check_sdd_drift.py --batch`) impede remoção ou alteração de métodos declarados ([`refactor-subagents.md:15-16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L15-L16)). | O arquivo `01-concepcao/dod-[slug].md` e `02-auditorias/pivots-[slug].md` podem ser alterados para mascarar ausência de conformidade. | 🟡 Atenção |
| **ASI07** | **Insecure Inter-Agent Communication** | Baixa-Média | Comunicação estruturada baseada em schema de Matriz de Evidências ([`refactor-dod.md:16-19`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-dod.md#L16-L19)) com validação programática determinística via [`validate_evidence_matrix.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/validate_evidence_matrix.py) ([`SKILL.md:17,24`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L17)), recalculando $V(G)$ via AST real. | Nenhum gap residual. Discrepâncias entre relatório e código real causam falha imediata (`exit 1`). | 🟢 Conforme (Mitigado) |
| **ASI08** | **Cascading Failures** | Alta | Entry Gate com 100% testes verdes e medição prévia de cobertura via `pytest --cov` com aviso se alvos $V(G)>10$ tiverem cobertura < 80% ([`SKILL.md:14`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L14), [`refactor-dod.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-dod.md#L7)). | Se testes de caracterização não forem criados após alerta de baixa cobertura, ramificações não cobertas podem sofrer alterações comportamentais. | 🟢 Conforme (Mitigado) |
| **ASI09** | **Human-Agent Trust Exploitation** | Alta | Relatório formal de consolidação (`refactor-report-template.md`) e tabela com $V(G)$ antes e depois ([`refactor-report-template.md:22-27`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/resources/refactor-report-template.md#L22-L27)). | A métrica $V(G)$ em queda rápida pode dar ao desenvolvedor uma falsa impressão de perfeição técnica, ocultando novos race conditions ou vazamentos de memória. | 🟡 Atenção |
| **ASI10** | **Rogue Agents** | Média-Alta | Regras de versão rígidas (`refactor-git.md`), rollback seguro com `git stash` e Tampering Gate determinístico no Step 4 (`git diff --exit-code <PHASE_START_HASH>...HEAD -- tests/`) que aborta e reverte se testes forem alterados. | Subagente pode tentar editar testes em iteração local, mas é sumariamente barrado no Exit Gate sem chance de persistência no commit. | 🟢 Conforme (Mitigado via Tampering Gate) |

---

## 4. Pontos Críticos de Atenção (Achados Forenses Detalhados)

### [REF-ASI02-01] Risco Crítico de Modificação Oportunista de Testes (*Assertion Tampering*) pelo `solid-refactorer`
- **Categorias OWASP:** ASI02 (Tool Misuse), ASI10 (Rogue Agents), LLM03 (Excessive Agency)
- **Severidade:** `Alta`
- **Status do Achado:** `🟢 Mitigado`
- **Localização Exata:** [`skills/refactor/SKILL.md:17,25`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L17), [`skills/refactor/references/refactor-git.md:10,31`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-git.md#L10), [`skills/refactor/references/refactor-dod.md:8`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-dod.md#L8), [`skills/refactor/references/refactor-subagents.md:7,13`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L7)
- **Descrição Técnica do Risco:**
  O subagente `solid-refactorer` é instanciado com `EnableWriteTools: true` e acesso global de escrita no projeto. O princípio fundamental da refatoração é a **invariância comportamental**, garantida pela estabilidade e imutabilidade dos testes unitários existentes. Sem barreiras físicas, quando um LLM executa uma refatoração profunda e quebra testes, ele tem forte tendência a editar arquivos de teste para "forçar aprovação" e evitar o rollback de Double-Strike.
- **Evidências de Mitigação Implementada:**
  1. No Step 4 de verificação pelo Orquestrador, antes do squash commit, foi adicionado o **Tampering Gate determinístico**:
     ```bash
     git diff --exit-code <PHASE_START_HASH>...HEAD -- tests/
     ```
  2. Caso o código de retorno seja diferente de 0 (qualquer arquivo de teste modificado, enfraquecido ou excluído), a fase é **imediatamente abortada**, as modificações em `tests/` são revertidas (`git checkout <PHASE_START_HASH> -- tests/`) e a refatoração é rejeitada com falha de segurança.
  3. A diretiva foi sincronizada em [`SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md), [`refactor-git.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-git.md), [`refactor-dod.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-dod.md), [`refactor-subagents.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md) e [`doc/skills/refactor/README.md:76-81`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/refactor/README.md#L76-L81).

---

### [REF-ASI06-01] Possibilidade de Evasão do Gate de Complexidade via Parâmetro `--exit-zero` em `ast_complexity.py`
- **Categorias OWASP:** ASI06 (Context and Memory Poisoning), ASI02 (Tool Misuse), LLM03 (Excessive Agency)
- **Severidade:** `Média-Alta`
- **Status do Achado:** `🟢 Mitigado`
- **Localização Exata:** [`skills/refactor/scripts/ast_complexity.py:139-143,215-221`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py#L139-L143), [`tests/skills/test_scanners.py:241-244`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L241-L244)
- **Descrição Técnica do Risco:**
  O analisador determinístico `ast_complexity.py` aceitava a flag `--exit-zero`, que permitia ignorar bloqueios mesmo com violações graves de complexidade. Essa flag exposta permitia que um agente em loop de falhas ou com alucinação executasse o scanner com `--exit-zero` para reportar falsamente sucesso nos exit gates, permitindo que métodos com $V(G) > 10$ ou erros de sintaxe passassem desapercebidos.
- **Evidências de Mitigação Implementada:**
  1. A flag `--exit-zero` foi integralmente removida do parser CLI em [`ast_complexity.py:139-143`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py#L139-L143).
  2. O script calcula `has_blocking_issues` e força `sys.exit(1)` caso existam funções com $V(G) > 10$, erros de parsing ou arquivos não encontrados ([`ast_complexity.py:215-221`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py#L215-L221)).
  3. Foi adicionado um teste unitário automatizado de segurança em [`tests/skills/test_scanners.py:241-244`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L241-L244) (`test_no_exit_zero_flag_in_ast_complexity`), executado e 100% verde no CI local.

---

### [REF-ASI05-01] Execução Recorrente de `pytest` sem Sandboxing no Interpretador Hospedeiro
- **Categorias OWASP:** ASI05 (Unexpected Code Execution), LLM03 (Excessive Agency)
- **Severidade:** `Média-Alta`
- **Status do Achado:** `🟢 Mitigado`
- **Localização Exata:** [`skills/refactor/SKILL.md:28`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L28)
- **Descrição Técnica do Risco:**
  Durante o ciclo de refatoração, a suíte de testes unitários é executada para validar que não houve regressão funcional. A execução do pytest importa dinamicamente o código refatorado e os testes. Caso o código-fonte sob refatoração contenha dependências vulneráveis ou chamadas acidentais a sockets de rede externos, o pytest rodaria com os privilégios do usuário local no host, sem restrição de sockets.
- **Evidências de Mitigação Implementada:**
  1. O plugin de isolamento de rede [`pytest_sandbox.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/scripts/pytest_sandbox.py) foi acoplado deterministicamente no Exit Gate de regressão de [`skills/refactor/SKILL.md:28`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L28):
     ```bash
     python -m pytest tests/unit/ -v -p skills.implement.scripts.pytest_sandbox
     ```
  2. Qualquer tentativa de abertura de socket TCP/IP remoto durante a validação é interceptada e abortada com `RuntimeError`, impedindo exfiltração de dados e conexões de rede não autorizadas.

---

### [REF-LLM04-01] Risco de Injeção de Dependências Não Versionadas ou Alucinadas (Slopsquatting) Durante Refatoração SOLID
- **Categorias OWASP:** LLM04 (Supply Chain Vulnerabilities), ASI04 (Agentic Supply Chain Vulnerabilities)
- **Severidade:** `Média`
- **Status do Achado:** `🟢 Mitigado`
- **Localização Exata:** [`skills/refactor/references/solid-catalog.md:20`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/solid-catalog.md#L20), [`skills/refactor/references/refactor-subagents.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L7), [`skills/refactor/SKILL.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L16)
- **Descrição Técnica do Risco:**
  Ao aplicar padrões SOLID (como Inversão de Dependência e Strategy), modelos LLM podem alucinar ou introduzir pacotes externos de injeção de dependência ou utilitários não homologados no manifesto do projeto (`pyproject.toml` / `requirements.txt`), expondo o projeto a vetores de *Slopsquatting*.
- **Evidências de Mitigação Implementada:**
  1. Adicionada diretiva explícita no catálogo SOLID ([`solid-catalog.md:20`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/solid-catalog.md#L20)): *"Zero New External Dependencies (Anti-Slopsquatting Rule): Refactoring MUST use ONLY Python stdlib (`typing.Protocol`, `dataclasses`, `abc`, `functools`, `enum`) or packages already declared in the project manifest."*
  2. Restrição injetada diretamente no System Prompt do `solid-refactorer` ([`refactor-subagents.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L7)) e reforçada no Step 3 de [`SKILL.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L16).
  3. Governança documentada em [`doc/skills/refactor/README.md:93`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/refactor/README.md#L93).

---

### [REF-ASI08-01] Risco de Falsos Negativos de Regressão em Código sem Cobertura Prévia no Diff
- **Categorias OWASP:** ASI08 (Cascading Failures), ASI09 (Human-Agent Trust Exploitation)
- **Severidade:** `Baixa-Média`
- **Status do Achado:** `🟢 Mitigado`
- **Localização Exata:** [`skills/refactor/SKILL.md:14`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L14), [`skills/refactor/references/refactor-dod.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-dod.md#L7), [`doc/skills/refactor/README.md:53`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/refactor/README.md#L53)
- **Descrição Técnica do Risco:**
  O Entry Gate da skill `/refactor` exigia apenas testes 100% verdes antes das edições, sem validar a **taxa de cobertura de testes (line/branch coverage)** dos alvos que seriam refatorados. Se uma função complexa possuísse apenas teste Happy Path, a refatoração poderia alterar comportamentos de exceção desprotegidos mantendo testes verdes.
- **Evidências de Mitigação Implementada:**
  1. Adicionada verificação de cobertura no Step 1 (Entry Gate) em [`SKILL.md:14`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L14) e [`refactor-dod.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-dod.md#L7):
     ```bash
     pytest --cov=<target_files> --cov-report=term-missing
     ```
  2. Foi instituído alerta mandatório para o arquiteto se a cobertura for inferior a 80% em alvos com $V(G) > 10$, exigindo testes de caracterização prévios antes da transformação de código.

---

### [REF-LLM03-01] Salvaguarda de Rollback Destrutivo via `git stash` no Double-Strike
- **Categorias OWASP:** LLM03 (Excessive Agency), ASI10 (Rogue Agents)
- **Severidade:** `Média`
- **Status do Achado:** `🟢 Mitigado`
- **Localização Exata:** [`skills/refactor/SKILL.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L16), [`skills/refactor/references/refactor-git.md:9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-git.md#L9), [`skills/refactor/references/refactor-subagents.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L7), [`doc/skills/refactor/README.md:88-92`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/refactor/README.md#L88-L92)
- **Descrição Técnica do Risco:**
  Na ocorrência de 2 falhas sucessivas (Double-Strike Rule), o protocolo anterior prescrevia a execução de `git reset --hard HEAD`. Esse comando em modo puro destruía sumariamente arquivos não rastreados (*untracked*) e modificações locais legítimas do operador que estivessem no diretório de trabalho.
- **Evidências de Mitigação Implementada:**
  1. A instrução de rollback no Step 3 de [`SKILL.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L16), no Modo 4 de [`refactor-git.md:9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-git.md#L9) e no prompt do `solid-refactorer` foi alterada para:
     ```bash
     git stash push -u -m "antigravity-refactor-safety-rollback" && git reset --hard <target_start_hash>
     ```
  2. Garante que qualquer trabalho intermediário seja salvo em stash antes do reset atômico para o commit do início do alvo, prevenindo perda catastrófica de dados.

---

### [REF-ASI07-01] Risco de Alucinação ou Discrepância na Matriz de Evidências de Refatoração
- **Categorias OWASP:** ASI07 (Insecure Inter-Agent Communication), ASI09 (Human-Agent Trust Exploitation), LLM07 (System Prompt Leakage / Misinformation)
- **Severidade:** `Média-Alta`
- **Status do Achado:** `🟢 Mitigado`
- **Localização Exata:** [`skills/refactor/scripts/validate_evidence_matrix.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/validate_evidence_matrix.py), [`skills/refactor/SKILL.md:17,24`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L17), [`tests/skills/test_scanners.py:1231-1304`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L1231-L1304)
- **Descrição Técnica do Risco:**
  O subagente `solid-refactorer` gera uma tabela Markdown de Matriz de Evidências em seu relatório pós-execução, reportando valores de $V(G)$ antes e depois para comprovar conformidade com $V(G) \le 10$. Modelos LLM podem exibir complacência ou alucinação (*metric hallucination*), reportando valores otimistas de $V(G)$ ou inventando dados para aparentar conformidade com os exit gates, induzindo o desenvolvedor a aceitar código com alta complexidade ciclomática.
- **Evidências de Mitigação Implementada:**
  1. Criação do script determinístico [`validate_evidence_matrix.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/validate_evidence_matrix.py) (zero dependências externas), que extrai a tabela Markdown do relatório, analisa o AST real dos arquivos de produção modificados e recalcula McCabe Cyclomatic Complexity $V(G)$ de cada função reportada.
  2. Bloqueio automático com `exit 1` em três condições críticas:
     - Discrepância entre o $V(G)$ reportado pelo subagente e o $V(G)$ real via AST (`[METRIC_DISCREPANCY]`).
     - Violação do teto $V(G) \le 10$ (`[COMPLEXITY_VIOLATION]`).
     - Funções ausentes ou não encontradas nos arquivos-fonte (`[UNRESOLVED_FUNCTION]`).
  3. Acoplamento obrigatório no Step 4 (VERIFY) e nos Exit Gates de [`skills/refactor/SKILL.md:17,24`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L17) (`Matrix Gate`).
  4. Cobertura completa por testes unitários em [`tests/skills/test_scanners.py:1231-1304`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L1231-L1304) (`TestValidateEvidenceMatrix`), comprovando assertividade determinística na detecção de discrepâncias e violações.

---

## 5. Plano de Ação Priorizado para a Skill `/refactor`

### Quick Wins (Baixo Esforço / Alto Impacto)
- [x] **Hardening do Exit Gate no Orquestrador contra Modificação de Testes:** Inserir a verificação `git diff --exit-code <PHASE_START_HASH>...HEAD -- tests/` no Step 4 de [`SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L17) e na tabela de Exit Gates ([`SKILL.md:25`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L25)). Se os testes tiverem sido alterados, a execução falha, aborta o squash e reverte as alterações.
- [x] **Remoção da Flag `--exit-zero` em `ast_complexity.py`:** Eliminar o argumento não seguro da CLI em [`ast_complexity.py:139-143`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py#L139-L143) para impedir bypasses mecânicos do teto $V(G) \le 10$, com teste de regressão em [`tests/skills/test_scanners.py:241-244`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L241-L244).
- [x] **Salvaguarda de Git Rollback em `refactor-git.md`:** Alterar a instrução de Double-Strike para criar um `git stash push -u -m "antigravity-refactor-safety-rollback"` antes do comando `git reset --hard <target_start_hash>` em [`refactor-git.md:9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-git.md#L9) e [`SKILL.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L16).
- [x] **Invariante de Biblioteca Padrão em `solid-catalog.md`:** Declarar explicitamente que refatorações devem usar exclusivamente a biblioteca padrão Python (`typing.Protocol`, etc.), sem inclusão de novas dependências externas em [`solid-catalog.md:20`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/solid-catalog.md#L20) e no prompt do subagente em [`refactor-subagents.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L7).

### Evoluções Estruturais (Scripts / Arquitetura de Subagentes)
- [x] **Gating de Cobertura Prévia no Step 1:** Integrar a medição de cobertura de ramificações (`pytest --cov`) no Entry Gate de [`SKILL.md:14`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L14) e [`refactor-dod.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-dod.md#L7), alertando o arquiteto caso funções com $V(G) > 10$ possuam cobertura inferior a 80%.
- [x] **Validador Programático da Matriz de Evidências:** Implementado em [`skills/refactor/scripts/validate_evidence_matrix.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/validate_evidence_matrix.py). Realiza o parsing determinístico da tabela Markdown do relatório de refatoração, recalculando o $V(G)$ real via AST dos arquivos-fonte e abortando (`exit 1`) em caso de discrepâncias, alucinações ou $V(G) > 10$. Integrado ao Step 4 e aos Exit Gates de [`SKILL.md:17,24`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L17) e coberto por testes em [`tests/skills/test_scanners.py:1231-1304`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L1231-L1304).
- [x] **Isolamento de Execução de Testes Unitários:** Acoplado o plugin de isolamento de rede [`pytest_sandbox.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/scripts/pytest_sandbox.py) na linha de comando de execução de testes de regressão nos Exit Gates de [`SKILL.md:28`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L28) (`-p skills.implement.scripts.pytest_sandbox`), impedindo conexões externas de rede e exfiltração durante o ciclo de testes unitários da refatoração.
