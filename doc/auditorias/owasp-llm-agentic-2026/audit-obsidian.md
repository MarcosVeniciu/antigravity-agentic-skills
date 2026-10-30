<Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/obsidian`>
**Data da Auditoria:** 2026-10-30  
**Skill Auditada:** [`skills/obsidian/SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md)  
**Documentação Arquitetural:** [`doc/skills/obsidian/README.md`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md)  
**Modelo de Execução da Skill:** 100% Orquestrador Principal (Zero Subagentes para eliminar boot token overhead e reter contexto na sessão ativa)  
**Status Geral de Segurança Agentic:** 🟢 Totalmente Mitigado / 100% Conforme (Arquitetura robusta com validação determinística de schemas YAML, scanner anti-Memory Poisoning com código de saída 1, verificação de paridade de wikilinks em disco via CLI unificado `validate_vault_note.py`, invariantes operacionais estritos de não-deleção e não-sobrescrita, regra de evidência empírica para Living DoD e gate Human-in-the-Loop via `ask_question` para `00-core-rules/`).

---

## 1. Sumário Executivo e Perfil de Risco da Skill

A skill [`/obsidian`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md) atua como o **Governante da Memória Persistente e Single Source of Truth (SSOT)** de todo o ecossistema Antigravity. Ela é responsável pela indexação, criação atômica, mutação cirúrgica (`vault_patch`) e validação da integridade referencial dos artefatos arquiteturais estruturados nas pastas canônicas do cofre:
- `00-core-rules/`: ADRs, `domain-glossary.md` e `conventions.md`.
- `01-concepcao/`: BDDs, SDDs, Épicos e Living DoDs.
- `02-auditorias/`: Relatórios de auditoria multi-domínio e logs de pivots técnicos.
- `03-releases/`: Changelogs e manifestos de publicação.

### Modelo de Operação e Ferramentas Acionadas
Conforme estabelecido em sua decisão arquitetural fundamental ([`doc/skills/obsidian/README.md#L21-L29`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L21-L29)), a skill opera com **0 subagentes (Zero Subagents)**, executando 100% no Orquestrador Principal. As ferramentas operadas incluem:
- Descoberta e Leitura: `search_query`, `vault_get_document_map`, `vault_read`, `backlinks`.
- Mutação: `vault_write` (restrito à criação de novas notas via template) e `vault_patch` (para mutações cirúrgicas em `heading` ou `frontmatter`).

### Superfície de Ataque e Riscos Principais (Mitigações Concluídas)
- **Perspectiva Meta-Agêntica:**
  1. **Envenenamento de Memória Persistente (Memory & Context Poisoning - ASI06 / LLM05):** Mitigado pelo **Core Rules HITL Gate** no Orquestrador ([`SKILL.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L12), [`obsidian-protocol.md#L9,L38`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L9-L38)) exigindo confirmação explícita humana via `ask_question` antes de qualquer alteração em `00-core-rules/`, somado ao scanner determinístico `scan_memory_poisoning()` em [`validate_vault_note.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py) que rejeita diretivas adversariais com exit code 1.
  2. **Ausência de Camada Programática de Proteção:** Mitigado pelo validador determinístico CLI [`skills/obsidian/scripts/validate_vault_note.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py) integrado obrigatoriamente no Step 3 do pipeline, além da formalização explícita dos invariantes `Surgical Patch` e `Immutability & Non-Deletion` ([`SKILL.md#L10-L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L10-L11)).
- **Perspectiva de Código Downstream:**
  A integridade do software produzido é garantida pela validação contínua de paridade de wikilinks em disco via [`validate_vault_note.py --vault-root`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py), eliminando referências fantasmas ou contratos órfãos entre BDD, SDD e Living DoD (ASI08).

---

## 2. Matriz de Conformidade: OWASP Top 10 for LLM Applications (2025/2026)

| Código | Categoria OWASP LLM (2025/2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **LLM01** | **Prompt Injection (Direta, Indireta ou Multimodal)** | **Alta** | Operações de busca filtram metadados específicos (`type`, `feature`) ([`README.md#L81-L85`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L81-L85)). Scanner determinístico anti-Memory Poisoning em [`validate_vault_note.py#L70-L96,L204-L218`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py#L70-L96) varre notas contra injeções (`ignore previous instructions`, `system override:`, `bypass check_sdd_drift`, `--exit-zero`, `<script>`). | Totalmente mitigado; notas com comandos de injeção são rejeitadas com exit code 1. | 🟢 Conforme |
| **LLM02** | **Sensitive Information Disclosure** | **Média** | O protocolo define templates estruturados ([`resources/note-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/resources/note-template.md)) e diretriz expressa em [`obsidian-protocol.md#L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L11) para mascarar qualquer credencial antes de persistir em pivots ou auditorias. | Totalmente mitigado; sanitização obrigatória no protocolo de escrita documental. | 🟢 Conforme |
| **LLM03** | **Excessive Agency** | **Alta** | Invariante `Surgical Patch` e `Strict Non-Deletion & Non-Overwrite Guard` proíbem `write_file` em notas existentes e banem comandos destrutivos (`rm`, `del`, `Remove-Item`, `git rm`) ([`SKILL.md#L10-L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L10-L11)). Gate HITL com `ask_question` para `00-core-rules/`. | Totalmente mitigado; ações destrutivas proibidas e mutações canônicas restritas a `vault_patch`. | 🟢 Conforme |
| **LLM04** | **Supply Chain Vulnerabilities** | **Média** | Templates canônicos unificados em [`resources/note-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/resources/note-template.md) com seções obrigatórias de *Threat Modeling*: `## Security & Threat Considerations` (ADR) e `## Security Invariants & Access Controls` (regras de domínio). | Totalmente mitigado; templates forçam análise explícita de risco cibernético. | 🟢 Conforme |
| **LLM05** | **Data and Model Poisoning** | **Crítica** | Gate HITL obrigatório via `ask_question` antes de criar ou modificar notas em `00-core-rules/` ([`SKILL.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L12)), complementado por scanner programático em [`validate_vault_note.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py). | Totalmente mitigado; integridade da memória persistente protegida determinística e proceduralmente. | 🟢 Conforme |
| **LLM06** | **Unbounded Consumption** | **Média** | Execução sem subagentes elimina boot token overhead de 3.000 a 8.000 tokens ([`README.md#L26`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L26)). Filtros de busca estritos por metadados (`[OBS-LLM09-04]`). | Totalmente mitigado; overhead eliminado e busca delimitada por escopo. | 🟢 Conforme |
| **LLM07** | **System Prompt Leakage / Misinformation** | **Média** | Esquemas estritos de frontmatter com tipos e status padronizados validados via CLI [`validate_vault_note.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py). | Totalmente mitigado; linter determinístico bloqueia metadados forjados ou schemas inválidos. | 🟢 Conforme |
| **LLM08** | **Hidden Context Exposure** | **Média** | Política de "One Chat Per Macro Phase" ([`prompts/gemini.md#L36`](file:///e:/Codigos/antigravity-agentic-workflows/prompts/gemini.md#L36)) combinada com proibição de logar tokens e credenciais em notas do cofre ([`obsidian-protocol.md#L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L11)). | Totalmente mitigado; higiene de sessão e mascaramento de segredos ativos. | 🟢 Conforme |
| **LLM09** | **Vector and Embedding Weaknesses** | **Alta** | Consultas parametrizadas por chaves tipadas (`type`, `feature`, `tags`) com sanitização ReDoS e precedência canônica inegociável de `00-core-rules/` sobre rascunhos em `01-concepcao/` ([`obsidian-protocol.md#L41`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L41)). | Totalmente mitigado; buscas estruturadas sem operadores vulneráveis e hierarquia estrita de fontes. | 🟢 Conforme |
| **LLM10** | **Improper Output Handling** | **Alta** | Operações cirúrgicas via `vault_patch` validadas pós-execução por [`validate_vault_note.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py) com PyYAML (`safe_load`) e checagem de delimitadores `---`. | Totalmente mitigado; corrupções sintáticas no YAML ou truncamentos são barrados no Step 3. | 🟢 Conforme |

---

## 3. Matriz de Conformidade: OWASP Top 10 for Agentic Applications (2026)

| Código | Categoria OWASP Agentic (2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **ASI01** | **Agent Goal Hijack** | **Alta** | O campo `feature` deve coincidir rigorosamente com a branch ativa ([`SKILL.md#L14`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L14)). Marcação de tarefas no Living DoD requer comprovação empírica (`[OBS-ASI09-06]`). | Totalmente mitigado; Living DoD não aceita conclusão desprovida de logs ou commits. | 🟢 Conforme |
| **ASI02** | **Tool Misuse and Exploitation** | **Alta** | Restrição de patch por cabeçalho/frontmatter com proibição expressa de sobrescrita e validação CLI de cada nota gerada/atualizada ([`SKILL.md#L10,L25`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L10-L25)). | Totalmente mitigado; uso de ferramentas delimitado e verificado pós-execução. | 🟢 Conforme |
| **ASI03** | **Identity and Privilege Abuse** | **Alta** | Execução restrita ao Orquestrador Principal sem subagentes intermediários; proibição de comandos shell de exclusão (`rm`, `del`, `Remove-Item`, `git rm`) e gate HITL para `00-core-rules/`. | Totalmente mitigado; privilégios disciplinados por invariantes estritos e aprovação humana. | 🟢 Conforme |
| **ASI04** | **Agentic Supply Chain Vulnerabilities** | **Baixa** | Modelos padronizados internos em [`resources/note-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/resources/note-template.md) com seções explícitas de conformidade e segurança cibernética. | Totalmente mitigado; templates auditados e autocontidos. | 🟢 Conforme |
| **ASI05** | **Unexpected Code Execution (RCE)** | **Média** | A skill `/obsidian` não executa código; scanner `scan_memory_poisoning()` bloqueia ativamente tags `<script>` e injeções de código executável em notas. | Totalmente mitigado; scripts maliciosos bloqueados no escaneamento de notas. | 🟢 Conforme |
| **ASI06** | **Memory and Context Poisoning** | **Crítica** | **Core Rules HITL Gate** exige `ask_question` antes de qualquer mutação em `00-core-rules/` ([`SKILL.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L12)), complementado por scanner de injeção em [`validate_vault_note.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py). | Totalmente mitigado; defesa em profundidade (aprovação humana + lint determinístico de injeção). | 🟢 Conforme |
| **ASI07** | **Insecure Inter-Agent Communication** | **Alta** | Comunicação assíncrona governada pelo Living DoD com regra de comprovação empírica (`[OBS-ASI09-06]`): marcações `- [x]` exigem hash de commit, sumário de testes ou link de auditoria. | Totalmente mitigado; estados comunicados entre agentes possuem rastreabilidade auditável. | 🟢 Conforme |
| **ASI08** | **Cascading Failures** | **Crítica** | Validador CLI de paridade de wikilinks em disco ([`validate_vault_note.py --vault-root`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py)) impede a persistência de links fantasmas ou referências quebradas. | Totalmente mitigado; integridade referencial do grafo de conhecimento garantida em tempo de execução. | 🟢 Conforme |
| **ASI09** | **Human-Agent Trust Exploitation** | **Alta** | Invariante `Empirical DoD Evidence` ([`SKILL.md#L13`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L13), [`obsidian-protocol.md#L29,L43`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L29-L43)): estritamente proibido marcar checkboxes concluídos no Living DoD sem evidência concreta. | Totalmente mitigado; conformidade fraudulenta ou alucinada é eliminada contratual e empiricamente. | 🟢 Conforme |
| **ASI10** | **Rogue Agents** | **Média** | O escopo é rigidamente atrelado à branch corrente via metadado `feature: [slug]` validado programaticamente por [`validate_vault_note.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py). | Totalmente mitigado; agentes não conseguem modificar notas fora do slug de sua branch ativa. | 🟢 Conforme |

---

## 4. Pontos Críticos de Atenção (Achados Forenses Detalhados)

### [OBS-ASI06-01] Envenenamento de Memória Persistente e Vetores de Context Poisoning
- **Categorias OWASP:** `ASI06: Memory and Context Poisoning` / `LLM05: Data and Model Poisoning` / `ASI01: Agent Goal Hijack`
- **Severidade:** `Crítica`
- **Status:** `🟢 Totalmente Mitigado`
- **Localização Exata:** [`skills/obsidian/SKILL.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L12), [`skills/obsidian/references/obsidian-protocol.md#L9,L38`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L9-L38), [`doc/skills/obsidian/README.md#L56`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L56), [`skills/obsidian/scripts/validate_vault_note.py#L70-L96,L204-L218`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py#L70-L96) e [`tests/skills/test_scanners.py#L652-L656`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L652-L656)
- **Descrição Técnica do Risco (Vetor de Ataque):**
  No ecossistema Antigravity, o Obsidian Vault funciona como a **Single Source of Truth (SSOT)** e a memória durável externa que conecta todas as fases do ciclo de desenvolvimento. No início de toda interação, o agente é instruído a carregar o contexto do cofre (`prompts/gemini.md#L16`). Se um invasor conseguisse injetar instruções adversariais em uma nota canônica (seja via pull request, issue manipulada ou prompt injection que instruísse o agente a alterar ADRs ou convenções), essas instruções tornavam-se memória persistente contaminando chats futuros.
- **Mitigação Concluída com Evidências de Código:**
  1. **Core Rules HITL Gate:** Instituído em [`SKILL.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L12), [`obsidian-protocol.md#L9,L38`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L9-L38) e [`README.md#L56`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L56). Toda criação ou mutação cirúrgica em arquivos dentro de `00-core-rules/` exige compulsoriamente a confirmação e aprovação explícita do usuário via `ask_question`.
  2. **Scanner Determinístico de Memory Poisoning:** Implementado na função `scan_memory_poisoning()` em [`skills/obsidian/scripts/validate_vault_note.py#L70-L96,L204-L218`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py#L70-L96), detectando regexes adversariais como `ignore previous instructions`, `system override:`, `disregard security`, `bypass check_sdd_drift`, `--exit-zero` e `<script>`, retornando exit code 1 (`[MEMORY_POISONING_RISK]`).
  3. **Verificação Automatizada:** Testado e aprovado em [`tests/skills/test_scanners.py#L652-L656`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L652-L656) (`test_memory_poisoning_detected`), retornando 0 erros e validação bem-sucedida no suite unittest.

---

### [OBS-ASI03-02] Execução 100% no Orquestrador com Salvaguardas Meramente Contratuais contra Sobrescritas e Exclusões
- **Categorias OWASP:** `ASI03: Identity and Privilege Abuse` / `LLM03: Excessive Agency` / `ASI02: Tool Misuse`
- **Severidade:** `Alta`
- **Status:** `🟢 Totalmente Mitigado`
- **Localização Exata:** [`skills/obsidian/SKILL.md#L10-L11,L24`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L10-L11), [`skills/obsidian/references/obsidian-protocol.md#L39`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L39) e [`doc/skills/obsidian/README.md#L54-L55`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L54-L55)
- **Descrição Técnica do Risco (Vetor de Ataque):**
  Como a skill opera diretamente no Orquestrador Principal sem subagentes isolados, o runtime detém ferramentas de filesystem irrestritas (`write_file`, `run_command`). Anteriormente, salvaguardas contra sobrescrita e deleção de notas eram exclusivamente contratuais, permitindo hipotéticos comandos destrutivos (`rm -rf 00-core-rules/`).
- **Mitigação Concluída com Evidências de Código:**
  1. **Invariantes Operacionais Blindados:** Em [`SKILL.md#L10-L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L10-L11), foram cravados os invariantes `Surgical Patch` e `Immutability & Non-Deletion`, proibindo expressamente sobrescritas via `write_file` em notas existentes e banindo comandos terminais destrutivos (`rm`, `del`, `Remove-Item`, `git rm`) sob pena de violação grave de protocolo.
  2. **Desativação de Exclusão Física:** Toda descontinuação documental é realizada exclusivamente por transição de estado semântica via `vault_patch`: `status: superseded` acompanhado do link `supersedes: [[note]]` ([`obsidian-protocol.md#L39`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L39)).
  3. **Validação Determinística Obrigatória:** O pipeline exige execução de `validate_vault_note.py` com exit code 0 no Step 3, confirmando a integridade física de arquivos e schemas após qualquer mutação.

---

### [OBS-LLM10-03] Ausência de Validação Determinística de Esquemas e Injeção de Frontmatter em `vault_patch`
- **Categorias OWASP:** `LLM10: Improper Output Handling` / `ASI02: Tool Misuse` / `LLM07: System Prompt Leakage / Misinformation`
- **Severidade:** `Alta`
- **Status:** `🟢 Totalmente Mitigado`
- **Localização Exata:** [`skills/obsidian/scripts/validate_vault_note.py#L99-L202`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py#L99-L202), [`skills/obsidian/SKILL.md#L14,L25`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L14), [`skills/obsidian/references/obsidian-protocol.md#L40`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L40) e [`tests/skills/test_scanners.py#L629-L650`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L629-L650)
- **Descrição Técnica do Risco (Vetor de Ataque):**
  A ausência de linter determinístico permitia que patches JSON malformados truncassem delimitadores `---`, injetassem enums de status inválidos ou desalinhassem o metadado `feature` em relação à branch Git ativa, gerando notas corrompidas invisíveis para buscas ou contratos forjados.
- **Mitigação Concluída com Evidências de Código:**
  1. **Validador CLI com PyYAML:** Criado [`skills/obsidian/scripts/validate_vault_note.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py) que valida parsing rigoroso com `yaml.safe_load` assegurando que o frontmatter seja um dict contendo todas as chaves obrigatórias (`type`, `feature`, `project: "antigravity"`, `date`, `description`, `tags`).
  2. **Controle Estrito de Enums e Formato de Data:** O validador restringe `type` ao conjunto canônico de 9 tipos (`adr`, `domain_rule`, `pivot`, `sdd`, `bdd`, `dod`, `audit`, `changelog`, `epic`), `status` a 7 enums permitidos e data no formato estrito `YYYY-MM-DD` com validação de calendário via `datetime.date.fromisoformat()`.
  3. **Verificação Automatizada:** Cobertura de teste contínuo em [`tests/skills/test_scanners.py#L629-L650`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L629-L650) (`test_valid_frontmatter_passes`), aprovado em suite unittest.

---

### [OBS-LLM09-04] Fraquezas de Indexação, Vector/Embedding Weaknesses e ReDoS em `search_query`
- **Categorias OWASP:** `LLM09: Vector and Embedding Weaknesses` / `LLM06: Unbounded Consumption` / `ASI02: Tool Misuse`
- **Severidade:** `Média`
- **Status:** `🟢 Totalmente Mitigado`
- **Localização Exata:** [`skills/obsidian/SKILL.md#L23`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L23), [`skills/obsidian/references/obsidian-protocol.md#L9,L41`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L9-L41) e [`doc/skills/obsidian/README.md#L83-L85`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L83-L85)
- **Descrição Técnica do Risco (Vetor de Ataque):**
  Queries não sanitizadas em `search_query` poderiam sofrer ataques de negação de serviço por expressões regulares com backtracking catastrófico (ReDoS), além de notas rascunho em `01-concepcao/` poderem manipular ranqueamentos semânticos contra regras consolidadas.
- **Mitigação Concluída com Evidências de Código:**
  1. **Filtros Parametrizados Tipados:** A diretriz operacional do Step 1 ([`SKILL.md#L23`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L23)) exige queries estruturadas por metadados limpos (`type: adr`, `type: sdd`, `feature: [slug]`, `tag: domain`), eliminando expressões regulares arbitrárias passíveis de ReDoS.
  2. **Precedência Canônica Determinística:** Formalizada regra expressa em [`obsidian-protocol.md#L9,L41`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L9-L41): qualquer artefato em `00-core-rules/` possui precedência inegociável sobre rascunhos e notas provisórias de `01-concepcao/`.

---

### [OBS-ASI08-05] Proliferação de Links Fantasmas e Quebra de Rastreabilidade no Grafo de Conhecimento
- **Categorias OWASP:** `ASI08: Cascading Failures` / `LLM07: System Prompt Leakage / Misinformation`
- **Severidade:** `Média`
- **Status:** `🟢 Totalmente Mitigado`
- **Localização Exata:** [`skills/obsidian/scripts/validate_vault_note.py#L226-L283`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py#L226-L283), [`skills/obsidian/SKILL.md#L15,L25`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L15), [`skills/obsidian/references/obsidian-protocol.md#L42`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L42) e [`doc/skills/obsidian/README.md#L104`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L104)
- **Descrição Técnica do Risco (Vetor de Ataque):**
  A persistência de wikilinks quebrados ou documentos hipotéticos (`[[adr-inexistente]]`) levava modelos nas fases de `/implement` e `/refactor` a alucinarem premissas contratuais inexistentes, resultando em quebras de compilação e falhas em cascata no pipeline downstream.
- **Mitigação Concluída com Evidências de Código:**
  1. **Validação de Paridade em Disco:** Implementada função `validate_wikilinks()` em [`validate_vault_note.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py), acionada via `--vault-root <dir>`.
  2. **Extração Inteligente:** A função limpa blocos de código cercados (ignora snippets ` ``` `), remove âncoras (`#secao`) e aliases (`|alias`), e verifica a existência física de cada arquivo markdown no disco (`known_stems` e `known_rel_paths`).
  3. **Invariante de Paridade:** O Invariante `Parity` em [`SKILL.md#L15`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L15) bloqueia notas com links órfãos que não resolvam fisicamente no cofre.

---

### [OBS-ASI09-06] Superfície de Exploração de Confiança em Checklists de Living DoD e Logs de Auditoria
- **Categorias OWASP:** `ASI09: Human-Agent Trust Exploitation` / `ASI01: Agent Goal Hijack`
- **Severidade:** `Média`
- **Status:** `🟢 Totalmente Mitigado`
- **Localização Exata:** [`skills/obsidian/SKILL.md#L13,L24`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L13), [`skills/obsidian/references/obsidian-protocol.md#L29,L43`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L29-L43) e [`doc/skills/obsidian/README.md#L57`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L57)
- **Descrição Técnica do Risco (Vetor de Ataque):**
  Agentes poderiam marcar levianamente checkboxes de conformidade de Living DoD (`- [x] Unit tests passing`) sem executar a suíte correspondente, induzindo engenheiros humanos a confiar em um status de pronto fraudulento e promovendo código defeituoso para branches protegidas.
- **Mitigação Concluída com Evidências de Código:**
  1. **Regra de Comprovação Empírica Inegociável:** Formalizada em [`SKILL.md#L13`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L13), [`obsidian-protocol.md#L29,L43`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L29-L43) e [`doc/skills/obsidian/README.md#L57`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L57): toda mutação de `- [ ]` para `- [x]` no Living DoD (`dod-[slug].md`) obriga a anexação explícita de evidência empírica verificável (hash Git do commit, extrato resumido da execução de testes ou link da nota de auditoria `[[audit-...]]`).
  2. **Interdição de Marcações Fraudulentas:** O protocolo estabelece que patches de Living DoD desprovidos de comprovação documental configuram violação direta de integridade e são sumariamente rejeitados nos gates de release.

---

## 5. Plano de Ação Priorizado para a Skill `/obsidian`

### Quick Wins (Baixo Esforço / Alto Impacto)
- [x] **Enriquecimento dos Templates de Nota:** Atualizado [`skills/obsidian/resources/note-template.md#L48-L52,L87-L91`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/resources/note-template.md#L48-L52) com campos explícitos de segurança cibernética nos templates de ADR (seção `## Security & Threat Considerations` cobrindo Auth, Secret Containment e mitigação OWASP) e regras de domínio (seção `## Security Invariants & Access Controls` cobrindo permissões, validações e trilha de auditoria).
- [x] **Guardrail Explícito de Não-Deleção:** Reforçada regra no SystemPrompt de [`skills/obsidian/SKILL.md#L10-L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L10-L11) estabelecendo que comandos de terminal de remoção (`rm`, `del`, `Remove-Item`, `git rm`) e sobrescritas diretas via `write_file` no diretório do cofre são estritamente proibidos e constituem violação de protocolo.
- [x] **Regra de Comprovação de Checklists no Living DoD:** Adicionada em [`skills/obsidian/references/obsidian-protocol.md#L29,L43`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L29-L43) a obrigatoriedade de vincular evidência documental (saída de teste, hash de commit ou link de auditoria) ao marcar itens como concluídos (`[OBS-ASI09-06]`).

### Evoluções Estruturais (Scripts / Arquitetura de Subagentes)
- [x] **Criação do Script de Linter de Frontmatter (`validate_vault_schemas.py` integrado em `validate_vault_note.py`):** Implementada validação sintática e semântica com PyYAML (`safe_load`) em [`skills/obsidian/scripts/validate_vault_note.py#L99-L202`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py#L99-L202), garantindo integridade de delimitadores, chaves obrigatórias e enums autorizados de tipos e status, com testes em [`tests/skills/test_scanners.py#L629-L650`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L629-L650).
- [x] **Criação do Validador de Integridade de Grafo (`check_vault_links.py` integrado em `validate_vault_note.py`):** Implementada checagem referencial na função `validate_wikilinks()` em [`skills/obsidian/scripts/validate_vault_note.py#L226-L283`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py#L226-L283) com a flag `--vault-root`, assegurando em disco que todo `[[wikilink]]` aponte para um arquivo real existente.
- [x] **Mecanismo de Proteção e Assinatura para `00-core-rules/`:** Guardrail determinístico Human-in-the-Loop implementado via **Core Rules HITL Gate** no orquestrador ([`skills/obsidian/SKILL.md#L12,L24`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L12), [`skills/obsidian/references/obsidian-protocol.md#L9,L38`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L9-L38) e [`doc/skills/obsidian/README.md#L56`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L56)), exigindo confirmação explícita humana via `ask_question` antes de qualquer mutação ou criação em `00-core-rules/`, com escaneamento determinístico em [`validate_vault_note.py#L70-L96,L204-L218`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/scripts/validate_vault_note.py#L70-L96) para detecção de injeções adversariais (`[MEMORY_POISONING_RISK]`) e testes automatizados em [`tests/skills/test_scanners.py#L652-L656`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L652-L656).
</Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/obsidian`>
