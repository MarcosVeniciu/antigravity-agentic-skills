<Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/ask`>
**Data da Auditoria:** 2026-10-30  
**Skill Auditada:** [`skills/ask/SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md)  
**Documentação Arquitetural:** [`doc/skills/ask/README.md`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/ask/README.md)  
**Modelo de Execução da Skill:** Orquestrador Principal (Sessão Ativa) + Subagente Especializado Isolado `research` (`flash_lite`, `EnableWriteTools: false`)  
**Status Geral de Segurança Agentic:** 🟢 Totalmente Mitigado / 100% Conforme (100% das salvaguardas OWASP LLM & Agentic implementadas, incluindo validador estrito de schema JSON para comunicação inter-agente [ASI07/ASI01] e script determinístico de sanitização de tokens e segredos [LLM02]).

---

## 1. Sumário Executivo e Perfil de Risco da Skill

A skill [`/ask`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md) atua como o **Oráculo do Projeto (Project Oracle)** no framework SDD 2.0 da Antigravity. Sua missão fundamental é esclarecer dúvidas conceituais, contratuais, arquiteturais e de código sem poluir a janela de contexto principal do desenvolvedor e sem introduzir mutações acidentais no repositório.

### Modelo de Operação e Ferramentas Acionadas
O pipeline da skill estrutura-se em um **Firewall de Contexto Adaptativo com Roteamento em 2 Vias**:
1. **Ramo Rápido (*Direct Lookup*):** Consultas pontuais (1 a 2 arquivos conhecidos) são executadas diretamente pelo Orquestrador Principal utilizando [`view_file`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L22) ou [`grep_search`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L29).
2. **Ramo Amplo (*Broad Survey*):** Varreduras exploratórias (> 2 arquivos ou busca profunda cross-module/Vault) são delegadas ao subagente nativo **`research`**, parametrizado explicitamente no modelo [`"flash_lite"`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L31) com [`EnableWriteTools: false`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L31) e ferramental restrito (`grep_search`, `find_by_name`, `view_file`, `search_vault`). O subagente opera em sandbox de contexto e devolve unicamente um payload JSON validado (`status`, `files_scanned`, `evidence`, `summary`).

### Superfície de Ataque e Mitigações Implementadas
- **Perspectiva Meta-Agêntica:** A skill possui robusta postura defensiva ao isolar o subagente com modelo leve e desabilitar nativamente ferramentas de escrita. A exclusão mandatória de diretórios (`ExcludeDirs: [".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".pytest_cache"]`) previne esgotamento de contexto (DoS). A validação determinística de schema JSON (`validate_research_json()`) em `skills/ask/scripts/redact_sensitive_tokens.py` garante que qualquer texto conversacional ou injeção indireta vinda do subagente seja prontamente rejeitada. A sanitização de credenciais mascara segredos como `[REDACTED_SECRET]`.
- **Perspectiva de Código Downstream:** A postura de "Humildade Epistêmica" ([`SKILL.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L12)) e o registro de *Spec Drift* ([`ask-sources.md#L21`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L21)) previnem alucinações de regras de negócio. O agente anexa obrigatoriamente um banner `[⚠️ SECURITY WARNING: ...]` caso o código citado apresente vulnerabilidades óbvias (SQLi, command injection, credenciais hardcoded), prevenindo exploração de confiança humana (ASI09).

---

## 2. Matriz de Conformidade: OWASP Top 10 for LLM Applications (2025/2026)

| Código | Categoria OWASP LLM (2025/2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **LLM01** | **Prompt Injection (Direta, Indireta ou Multimodal)** | **Média** | O subagente [`research`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L29-L34) tem `EnableWriteTools: false` e SystemPrompt estrito; comentários de código são tratados como `<untrusted_data>`; saída do subagente é validada por schema JSON estrito (`validate_research_json()`), rejeitando texto livre. | Mitigado por schema JSON rígido e isolamento de sandbox. | 🟢 Conforme |
| **LLM02** | **Sensitive Information Disclosure** | **Alta** | Leitura restrita a `.env.example`/`.env.template` ([`ask-sources.md#L10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L10)); sanitização determinística obrigatória via [`redact_sensitive_tokens.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/scripts/redact_sensitive_tokens.py) para Bearer tokens, chaves OpenAI, Anthropic, Google, Stripe, GitHub, AWS, senhas DSN e JWTs. | Zero gaps residuais. Cobertura determinística com testes unitários. | 🟢 Conforme |
| **LLM03** | **Excessive Agency** | **Média** | Invariante `Read-Only` ([`SKILL.md#L10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L10)); subagente configurado com `EnableWriteTools: false` ([`SKILL.md#L31`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L31)). Proibição de CLI mutante e allowlist estrita do Git ([`ask-sources.md#L9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L9)). | Salvaguarda de prompt e allowlist Git bloqueiam comandos mutantes. | 🟢 Conforme |
| **LLM04** | **Supply Chain Vulnerabilities** | **Baixa** | Zero instalação de dependências ou execução de gerenciadores de pacotes ([`ask-sources.md#L9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L9)). | Nenhuma vulnerabilidade direta na skill. | 🟢 Conforme |
| **LLM05** | **Data and Model Poisoning** | **Média** | A skill é puramente consumidora (Read-Only) do Obsidian Vault e do código-fonte ([`ask-sources.md#L8`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L8)); não escreve no cofre nem em templates. Regra de Spec Drift mitiga contradições. | Tratamento de discrepâncias documentado. | 🟢 Conforme |
| **LLM06** | **Unbounded Consumption** | **Alta** | Uso de modelo enxuto [`"flash_lite"`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L31) para pesquisas amplas; exclusão mandatória de pastas gigantes `ExcludeDirs: [".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".pytest_cache"]`. | Mitigado por exclusão forçada de diretórios de build e dependências. | 🟢 Conforme |
| **LLM07** | **System Prompt Leakage / Misinformation** | **Média** | Invariante `Humility` ([`SKILL.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L12)) proíbe adivinhações e exige declaração expressa de gaps; citações formais auditáveis com linhas exatas ([`ask-sources.md#L36-L40`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L36-L40)). | Risco residual mínimo. | 🟢 Conforme |
| **LLM08** | **Hidden Context Exposure** | **Baixa** | Contexto do subagente é efêmero e isolado; apenas o payload JSON filtrado retorna para a sessão principal ([`README.md#L23`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/ask/README.md#L23)); tokens sensíveis são mascarados como `[REDACTED_SECRET]`. | Redação automática impede retenção de segredos no histórico. | 🟢 Conforme |
| **LLM09** | **Vector and Embedding Weaknesses** | **Baixa** | Uso de busca lexical por caminhos e metadados no cofre Obsidian ([`SKILL.md#L32`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L32)). | Riscos adversariais em notas minimizados pela checagem cruzada com código real. | 🟢 Conforme |
| **LLM10** | **Improper Output Handling** | **Baixa** | A saída da skill `/ask` é puramente conversacional/relatório markdown entregue ao usuário ([`README.md#L46`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/ask/README.md#L46)); não alimenta scripts de automação ou comandos CLI. | Nenhuma saída do `/ask` é canalizada sem supervisão para interpretadores de comandos ou bancos de dados. | 🟢 Conforme |

---

## 3. Matriz de Conformidade: OWASP Top 10 for Agentic Applications (2026)

| Código | Categoria OWASP Agentic (2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **ASI01** | **Agent Goal Hijack** | **Média** | O SystemPrompt de [`research`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L33) define escopo extremamente restrito; o payload devolvido é validado por schema JSON estrito (`validate_research_json()`), rejeitando qualquer texto conversacional ou diretiva injetada. | Mitigado por schema JSON fechado. | 🟢 Conforme |
| **ASI02** | **Tool Misuse and Exploitation** | **Média** | O subagente tem lista branca restrita de ferramentas de leitura (`grep_search`, `find_by_name`, `view_file`, `search_vault`) e exclusão obrigatória de pastas de sistema e credenciais. | Ferramental confinado a leituras necessárias. | 🟢 Conforme |
| **ASI03** | **Identity and Privilege Abuse** | **Média** | Subagente `research` opera com privilégios rebaixados (`flash_lite` com `EnableWriteTools: false`), impedindo mutações no workspace ([`SKILL.md#L31`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L31)). Orquestrador possui instrução explícita de guarda prévia e allowlist somente-leitura Git. | Confinamento ativo do subagente e diretivas de guarda no Orquestrador. | 🟢 Conforme |
| **ASI04** | **Agentic Supply Chain Vulnerabilities** | **Baixa** | O subagente utilizado é estático, nativo e configurado no repositório; não consome registries externos de agentes ou prompts remotos. | Risco residual padrão de provedor de nuvem. | 🟢 Conforme |
| **ASI05** | **Unexpected Code Execution (RCE)** | **Baixa** | Proibição explícita de comandos mutantes ([`ask-sources.md#L9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L9)); comandos permitidos são puramente diagnósticos (`git log`, `git status`, `git diff`, `git branch`). Subagente sem ferramenta `run_command`. | Impossibilidade de execução arbitrária no subagente. | 🟢 Conforme |
| **ASI06** | **Memory and Context Poisoning** | **Média** | Regra estrita de `Zero Vault Writes` ([`ask-sources.md#L8`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L8)); a skill não escreve nem altera notas no Obsidian. | Zero mutação de memória de longo prazo. | 🟢 Conforme |
| **ASI07** | **Insecure Inter-Agent Communication** | **Média** | Validação determinística de schema JSON (`validate_research_json()`) no Orquestrador sobre a saída de `research`. Exigência estrita dos campos `status`, `files_scanned`, `evidence` e `summary`. Qualquer payload livre ou malformado é sumariamente descartado. | Mitigado por validador programático determinístico. | 🟢 Conforme |
| **ASI08** | **Cascading Failures** | **Média** | Árvore de Decisão de Handover explícita ([`README.md#L89-L103`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/ask/README.md#L89-L103)) direciona o usuário para a skill correta (`/plan`, `/implement`, `/refactor`) em vez de agir diretamente. | Prevenção de decisões baseadas em premissas desatualizadas. | 🟢 Conforme |
| **ASI09** | **Human-Agent Trust Exploitation** | **Média** | Citações auditáveis obrigatórias com esquemas canônicos `file:///path#Lxx-Lyy` e `[[nota]]` ([`ask-sources.md#L36-L40`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L36-L40)) aliadas ao banner proativo `[⚠️ SECURITY WARNING: ...]`. | Desenvolvedor é alertado contra código legado vulnerável. | 🟢 Conforme |
| **ASI10** | **Rogue Agents** | **Baixa** | Subagente opera em ciclo único (Single-turn execution) e encerra imediatamente após emitir o JSON validado ([`SKILL.md#L33`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L33)). | Impossibilidade de loops autônomos desgovernados. | 🟢 Conforme |

---

## 4. Pontos Críticos de Atenção (Achados Forenses Detalhados)

### [ASK-LLM02-01] Exposição Irrestrita de Segredos e Arquivos `.env` no Tier 1 (Codebase Truth)
- **Categorias OWASP:** `LLM02: Sensitive Information Disclosure` / `ASI02: Tool Misuse`
- **Severidade:** `Alta` (Mitigada)
- **Localização Exata:** [`skills/ask/references/ask-sources.md#L18`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L18) e [`skills/ask/scripts/redact_sensitive_tokens.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/scripts/redact_sensitive_tokens.py)
- **Mitigação Implementada:**
  Substituída a leitura de `.env` real por `.env.example` e implementado o script determinístico `redact_sensitive_tokens.py`, que mascara Bearer tokens, OpenAI/Anthropic/Google/Stripe/GitHub/AWS keys, credenciais DSN e tokens JWT antes da renderização no chat principal (`[REDACTED_SECRET]`).

---

### [ASK-ASI03-02] Assimetria de Privilégios: Confinamento Estrito no Subagente vs. Ferramentas Mutantes Livres no Orquestrador
- **Categorias OWASP:** `LLM03: Excessive Agency` / `ASI03: Identity and Privilege Abuse`
- **Severidade:** `Média` (Mitigada)
- **Localização Exata:** [`skills/ask/SKILL.md#L10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L10) e [`skills/ask/references/ask-sources.md#L7-L9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L7-L9)
- **Mitigação Implementada:**
  Invariante Read-Only reforçado com proibição estrita de `write_file`/`edit_file` e restrição estrita do `run_command` à allowlist de leitura do Git (`git status`, `git log`, `git diff`, `git branch`).

---

### [ASK-LLM06-03] Consumo Ilimitado de Recursos por Varreduras em Diretórios Gigantes
- **Categorias OWASP:** `LLM06: Unbounded Consumption` / `ASI02: Tool Misuse`
- **Severidade:** `Média` (Mitigada)
- **Localização Exata:** [`skills/ask/SKILL.md#L34`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L34)
- **Mitigação Implementada:**
  Inclusão de cláusula mandatória de exclusão de diretórios:
  `ExcludeDirs: [".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".pytest_cache"]`.

---

### [ASK-ASI09-04] Risco de Chancelamento Acrítico de Código Vulnerável Existente sem Alerta de Segurança
- **Categorias OWASP:** `ASI09: Human-Agent Trust Exploitation` / `ASI08: Cascading Failures`
- **Severidade:** `Baixa` (Mitigada)
- **Localização Exata:** [`skills/ask/SKILL.md#L13`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L13) e [`skills/ask/references/ask-sources.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L12)
- **Mitigação Implementada:**
  Inclusão obrigatória de banner de alerta de segurança (`[⚠️ SECURITY WARNING: ...]`) sempre que o trecho de código citado contiver vulnerabilidades óbvias conhecidas.

---

## 5. Plano de Ação Priorizado para a Skill `/ask`

### Quick Wins (Baixo Esforço / Alto Impacto)
- [x] **Sanitização de `.env`:** Atualizar [`skills/ask/references/ask-sources.md#L18`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md#L18) para substituir `.env` por `.env.example` no Tier 1 e proibir formalmente a leitura ou citação de variáveis com valores em texto puro.
- [x] **Blacklist de Diretórios no Subagente `research`:** Adicionar no SystemPrompt de [`skills/ask/SKILL.md#L33`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/SKILL.md#L33) a cláusula de exclusão mandatória de `node_modules`, `.venv`, `.git` e pastas de artefatos de build.
- [x] **Alerta de Segurança na Síntese:** Inserir em [`skills/ask/references/ask-sources.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/ask/references/ask-sources.md) a regra de alerta proativo caso o código citado contenha vulnerabilidades óbvias de injeção ou exposição de credenciais.

### Evoluções Estruturais (Scripts / Arquitetura de Subagentes)
- [x] **Validador de Saída de Inter-Agent Communication:** Criar validação de schema para os dados devolvidos por `research`, garantindo que o subagente retorne estritamente um formato tabular estruturado, descartando payloads conversacionais ou tentativas de injeção indireta.
- [x] **Script de Sanitização de Respostas:** Desenvolver um script utilitário (`skills/ask/scripts/redact_sensitive_tokens.py`) para mascarar chaves de API, endereços IP internos e tokens JWT antes da renderização final no chat principal.
</Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/ask`>
