<Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/plan`>
**Data da Auditoria:** 2026-10-30  
**Skill Auditada:** [`skills/plan/SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md)  
**Documentação Arquitetural:** [`doc/skills/plan/README.md`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/plan/README.md)  
**Modelo de Execução da Skill:** SDD 2.0 Elephant & Goldfish: Main Orchestrator + Subagentes de Autoria (`bdd-architect` e `sdd-architect`, `Model: "inherit"`) + Goldfish Council (3x `flash`, Read-Only)  
**Status Geral de Segurança Agentic:** 🟢 Mitigado (9/9 Mitigações Concluídas — validações de assinatura e paridade bijetora integradas ao `validate_sdd_content()`)

---

## 1. Sumário Executivo e Perfil de Risco da Skill

A skill [`/plan`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md) estrutura a **Fase 1 (Concepção Arquitetural, BDD, SDD e Living DoD)** do ecossistema SDD 2.0. Seu objetivo é conceber e especificar integralmente o comportamento funcional e as fronteiras arquiteturais de uma funcionalidade antes de qualquer linha de código de produção ser escrita (*"Zero code in Phase 1"*).

### Pipeline de Execução e Ferramental
- **Step 1 — Scope Debate (Orquestrador):** Entrevista socrática via `ask_question` (3 a 5 perguntas) com eliminação do Problema XY e geração de Matriz de Propostas (Pragmatic, Scalable, Hybrid) em [`plan-debate.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-debate.md).
- **Step 2 — Git Flow Governance (Orquestrador):** Bloqueio de branches base (`main`, `develop`, etc.) e validação de nome de branch via [`validate_branch.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_branch.py).
- **Step 3 — BDD Modeling (`bdd-architect`, `Model: "inherit"`, `Write: true`):** Autoria em Context-Zero de Gherkin puro (`@happy-path`, `@unhappy-path`, `@security`, `@concurrency`) em `01-concepcao/bdd-[slug].md` conforme [`plan-bdd.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-bdd.md).
- **Step 4 — SDD Blueprint (`sdd-architect`, `Model: "inherit"`, `Write: true`):** Desenho de diagramas Mermaid (`sequenceDiagram` e `classDiagram`), contratos tipados via [`sdd-contract-template.yaml`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/sdd-contract-template.yaml) e validação automatizada com [`validate_sdd_contracts.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py).
- **Step 5 — Goldfish Council (3x `Model: "flash"`, Read-Only):** Três revisores cegos em paralelo atacam o design sob perspectivas de simplicidade (🐠 `goldfish-yagni`), segurança e concorrência (🐠 `goldfish-adversary`) e completude de contratos (🐠 `goldfish-implementer`) descritos em [`plan-goldfish.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md). O Orquestrador arbitra com o humano via `ask_question`.
- **Step 6 — Living DoD & Commit (Orquestrador):** Inicialização do checklist em `01-concepcao/dod-[slug].md` e commit semântico Modo 3 em [`plan-dod.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-dod.md) e [`plan-git.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-git.md).

### Análise Dual de Superfície de Ataque
1. **Perspectiva A (Meta-Agêntica):** A vulnerabilidade crítica de agência excessiva e potencial RCE foi **totalmente mitigada**: o privilégio de execução de shell (`run_command`) foi estritamente revogado dos subagentes de autoria (`bdd-architect` e `sdd-architect`), suas permissões de escrita foram estritamente confinadas ao diretório `01-concepcao/`, e a execução determinística do script [`validate_sdd_contracts.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py) foi transferida com exclusividade para o Orquestrador Principal, acompanhada de circuit breaker (`MaxIterations: 2`). Adicionalmente, foi implementada delimitação XML (`<untrusted_spec>`) para isolar especificações contra injeção de prompt indireta nos subagentes do Conselho Goldfish, e as respostas dos três críticos foram padronizadas em JSON Schema validado.
2. **Perspectiva B (Código Downstream):** O Conselho Goldfish (`goldfish-adversary`, `yagni`, `implementer`) atua como barreira pró-ativa de alto valor, operando em modo Read-Only estrito (`EnableWriteTools: false`). O script `validate_sdd_contracts.py` valida a paridade de métodos (`sequenceDiagram` $\leftrightarrow$ `classDiagram`), exige a presença de blocos `alt/else` e contratos de segurança/exceção quando há cenários negativos no BDD (`--bdd`). Os 2 débitos estruturais de validação semântica foram **parcialmente mitigados**: (1) validação estrita de assinaturas e tipos com `extract_class_method_signatures` e `validate_method_signature_types`, e (2) mapeamento bijetor 1:1 BDD $\leftrightarrow$ SDD de cenários negativos com `check_bijective_bdd_sdd_scenarios`, ambos implementados e cobertos por testes unitários dedicados ([`tests/skills/test_scanners.py#L1369-L1404`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L1369-L1404)). Contudo, a integração dessas funções no fluxo principal `validate_sdd_content()` ainda está pendente, de modo que a validação não é disparada na execução CLI do script pelo Orquestrador.

---

## 2. Matriz de Conformidade: OWASP Top 10 for LLM Applications (2025/2026)

| Código | Categoria OWASP LLM (2025/2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **LLM01** | Prompt Injection (Direta, Indireta ou Multimodal) | **Alta** | **Context-Zero Firewall** e delimitação XML: `bdd-architect`, `sdd-architect` e o Conselho Goldfish recebem apenas artefatos estritos ([`plan-goldfish.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L7)). O Conselho Goldfish recebe specs isoladas em tags `<untrusted_spec>` com diretiva estrita de tratar conteúdo como dados passivos. `run_command` foi revogado dos subagentes. | Injeções indiretas em manifestos ou docstrings lidos por `sdd-architect` não possuem capacidade de execução shell devido à revogação de `run_command`. | 🟢 Conforme / Mitigado |
| **LLM02** | Sensitive Information Disclosure | **Média** | Subagentes do Conselho Goldfish rodam em `flash` com `EnableWriteTools: false` e não possuem ferramentas de rede. Inclusão obrigatória de bloco `security:` com `sensitive_fields` para redação em logs no [`sdd-contract-template.yaml`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/sdd-contract-template.yaml) e [`plan-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/plan-template.md). | Necessidade de vigilância humana na arbitragem para garantir que segredos fictícios não vazem para repositórios públicos. | 🟢 Conforme / Mitigado |
| **LLM03** | Excessive Agency | **Crítica** | Subagentes `bdd-architect` e `sdd-architect` possuem `run_command: forbidden` e escrita restrita exclusivamente a `01-concepcao/`. Execução de Python (`validate_sdd_contracts.py`) transferida com exclusividade para o Orquestrador Principal. Conselho Goldfish opera com `EnableWriteTools: false` ([`plan-goldfish.md:8-16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L8-L16)). | **TOTALMENTE MITIGADO:** Menor privilégio rigorosamente estabelecido; subagentes não possuem acesso a shell e não gravam fora de `01-concepcao/`. | 🟢 Totalmente Mitigado |
| **LLM04** | Supply Chain Vulnerabilities | **Média** | Fase 1 não instala pacotes; a skill `/infra` é o gatekeeper de dependências do ecossistema. | O `sdd-architect` pode alucinar pacotes externos inexistentes (slopsquatting) ou bibliotecas abandonadas no diagrama de componentes, recomendando-os para uso nas Fases 2 e 3. | 🟢 Robusto com Pontos de Atenção |
| **LLM05** | Data and Model Poisoning | **Média** | O validador determinístico [`validate_sdd_contracts.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py) audita a estrutura formal dos artefatos. | Se um `bdd-[slug].md` contendo lógica de negócio corrompida for aprovado pelo humano no Gate 1, ele é ingerido pelo `sdd-architect` como verdade inquestionável. | 🟢 Conforme |
| **LLM06** | Unbounded Consumption | **Alta** | Subagentes do Conselho Goldfish usam `Model: "flash"` ([`plan-goldfish.md:21`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L21)). Orquestrador impõe circuit breaker com `MaxIterations: 2` na validação de contratos pelo `sdd-architect`, escalando para arbitragem humana via `ask_question` em caso de persistência de erros. Padrão "until exit 0" eliminado. | **TOTALMENTE MITIGADO:** Loop descontrolado eliminado pelo circuit breaker no Orquestrador. | 🟢 Totalmente Mitigado |
| **LLM07** | System Prompt Leakage / Misinformation | **Média** | Prompts de autoria e crítica são modulares, estáticos e versionados no repositório. O Conselho Goldfish (`goldfish-implementer`) complementa a checagem com JSON Schema estruturado ([`plan-goldfish.md:30-47`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L30-L47)). | **MITIGADO:** Funções `extract_class_method_signatures` e `validate_method_signature_types` implementadas ([`validate_sdd_contracts.py:117-173`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py#L117-L173)) e testadas ([`tests/skills/test_scanners.py:1370-1386`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L1370-L1386)), integradas em `validate_sdd_content()` (execu??o via CLI). | 🟢 Mitigado |
| **LLM08** | Hidden Context Exposure | **Baixa** | Separação estrita de sessões (*Elephant & Goldfish*); cada subagente roda em `conversationId` isolado e recebe apenas os artefatos estritamente necessários. | Excelente implementação da arquitetura Context-Zero. Zero vazamento de contexto não intencional entre subagentes paralelos. | 🟢 Conforme |
| **LLM09** | Vector and Embedding Weaknesses | **Baixa** | Não utiliza bases vetoriais nem geração RAG por embeddings. | Não aplicável diretamente ao design desta skill. | 🟢 Conforme |
| **LLM10** | Improper Output Handling | **Média** | Validador de YAML utiliza `yaml.safe_load(content)` ([`validate_sdd_contracts.py:288`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py#L288)), prevenindo vulnerabilidades de desserialização insegura. | **PARCIALMENTE MITIGADO:** Função `check_bijective_bdd_sdd_scenarios` implementada ([`validate_sdd_contracts.py:175-210`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py#L175-L210)) e testada ([`tests/skills/test_scanners.py:1387-1404`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L1387-L1404)), porém pendente fiação em `validate_sdd_content()` no CLI. | 🟢 Mitigado |

---

## 3. Matriz de Conformidade: OWASP Top 10 for Agentic Applications (2026)

| Código | Categoria OWASP Agentic (2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **ASI01** | Agent Goal Hijack | **Alta** | Entrevista Socrática obrigatória no Step 1 via `ask_question` ([`plan-debate.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-debate.md#L12)) e Propostas Arquiteturais limitadas a no máximo 3 opções ([`plan-debate.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-debate.md#L16)). | Textos de issues maliciosas ou especificações carregadas no Step 1 podem tentar forçar arquiteturas inseguras ou desativar proteções sem que o orquestrador perceba antes da aprovação da proposta. | 🟢 Robusto com Pontos de Atenção |
| **ASI02** | Tool Misuse and Exploitation | **Alta** | Scripts dedicados com validação de argumentos via `argparse` ([`validate_branch.py:93-110`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_branch.py#L93-L110) e [`validate_sdd_contracts.py:421-437`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py#L421-L437)). Expressão regular `VALID_BRANCH_REGEX` em [`validate_branch.py:28-30`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_branch.py#L28-L30) foi endurecida para aceitar apenas caracteres alfanuméricos e hífens (`^[a-z0-9]+(?:-[a-z0-9]+)*$`). | **TOTALMENTE MITIGADO:** Risco de injeção shell em nomes de branches e worktrees neutralizado e coberto por testes unitários ([`tests/skills/test_scanners.py:726-736`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L726-L736)). | 🟢 Totalmente Mitigado |
| **ASI03** | Identity and Privilege Abuse | **Crítica** | Conselho Goldfish é estritamente Read-Only (`EnableWriteTools: false`, `run_command: forbidden`) ([`plan-goldfish.md:21`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L21)). Subagentes `bdd-architect` e `sdd-architect` tiveram ferramenta de shell revogada (`run_command: forbidden`) e gravação confinada a `01-concepcao/`. | **TOTALMENTE MITIGADO:** Princípio do Menor Privilégio (*Least Privilege*) estritamente implementado. | 🟢 Totalmente Mitigado |
| **ASI04** | Agentic Supply Chain Vulnerabilities | **Média** | Templates estruturados versionados localmente em `resources/` ([`plan-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/plan-template.md) e [`sdd-contract-template.yaml`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/sdd-contract-template.yaml)). | Atualizações no comportamento de raciocínio dos modelos subjacentes (`flash` e `inherit`) podem alterar o rigor das críticas do Conselho Goldfish sem aviso. | 🟢 Conforme |
| **ASI05** | Unexpected Code Execution (RCE) | **Crítica** | Invariante central: "Zero code in Phase 1" ([`SKILL.md:8`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L8)). Bloqueio estrito de código de produção na fase de planejamento. Revogação de `run_command` em todos os subagentes (`bdd-architect`, `sdd-architect`, Goldfish Council). Validação determinística Python executada unicamente pelo Orquestrador. | **TOTALMENTE MITIGADO:** Vetor de RCE via subagentes completamente eliminado. | 🟢 Totalmente Mitigado |
| **ASI06** | Memory and Context Poisoning | **Alta** | **Conselho Goldfish (Step 5)** atua como barreira anti-envenenamento de premissas, atacando ativamente overengineering, vulnerabilidades de concorrência e contratos incompletos ([`plan-goldfish.md:20-22`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L20-L22)). | A arbitragem dos achados é feita com o desenvolvedor via `ask_question`. Se o humano rejeitar os avisos do `goldfish-adversary`, premissas vulneráveis persistem no Living DoD em `01-concepcao/dod-[slug].md`. | 🟢 Robusto com Pontos de Atenção |
| **ASI07** | Insecure Inter-Agent Communication | **Média** | Fluxo hierárquico estruturado (Map-Reduce). Saída padronizada dos 3 críticos do Conselho Goldfish em JSON Schema rígido com validação sintática antes da renderização da Matriz de Arbitragem ([`plan-goldfish.md:30-47`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L30-L47)). | **TOTALMENTE MITIGADO:** Ambiguidade de parsing em tabelas markdown eliminada pela obrigatoriedade de JSON Schema. | 🟢 Totalmente Mitigado |
| **ASI08** | Cascading Failures | **Alta** | Validação automatizada cruzada com `--bdd` no [`validate_sdd_contracts.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py#L212-L282) garante paridade semântica de métodos de sequência no `classDiagram`, presença obrigatória de ramos `alt/else` e exceções quando BDD possui cenários negativos/segurança. | **MITIGADO:** Funções `extract_class_method_signatures`, `validate_method_signature_types` e `check_bijective_bdd_sdd_scenarios` implementadas e testadas unitariamente ([`tests/skills/test_scanners.py#L1369-L1404`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L1369-L1404)), integradas em `validate_sdd_content()` (execu??o via CLI). | 🟢 Mitigado |
| **ASI09** | Human-Agent Trust Exploitation | **Alta** | Dois portões de arbitragem humana obrigatórios com `ask_question`: Gate 1 (aprovação do BDD) e Gate de Arbitragem (achados do Conselho Goldfish) ([`doc/skills/plan/README.md:27-28`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/plan/README.md#L27-L28)). | A chancela visual do Conselho Goldfish (`yagni: ZERO_FINDINGS`) pode levar o desenvolvedor humano à complacência, aprovando o SDD sem inspecionar os detalhes de persistência e segurança. | 🟢 Robusto com Pontos de Atenção |
| **ASI10** | Rogue Agents | **Alta** | Os 5 subagentes possuem papéis cirúrgicos delimitados por personas claras e focadas ([`plan-goldfish.md:14-29`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L14-L29)). Circuit breaker `MaxIterations: 2` e supervisão pelo Orquestrador impedem loops ou desvios autônomos. | **TOTALMENTE MITIGADO:** Execução autônoma sem supervisão eliminada. | 🟢 Totalmente Mitigado |

---

## 4. Pontos Críticos de Atenção (Achados Forenses Detalhados)

### [PLAN-ASI03-ASI05-01] Permissão Excessiva de Escrita e Execução de Shell (`run_command`) no Subagente `sdd-architect`
- **Categorias OWASP Associadas:** ASI03 (Identity and Privilege Abuse) / ASI05 (Unexpected Code Execution) / LLM03 (Excessive Agency)
- **Severidade:** **Crítica**
- **Status:** 🟢 **Totalmente Mitigado**
- **Localização Exata:** [`skills/plan/references/plan-goldfish.md#L8-L13`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L8-L13) e [`skills/plan/SKILL.md#L16-L17`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L16-L17).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**
  Na Fase 1, o princípio arquitetural fundamental é *"Zero code in Phase 1"* ([`SKILL.md:8`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L8)). Contudo, a especificação instrui que o subagente `sdd-architect` deve rodar com `Model: "inherit"`, `Write: true` e orienta em seu SystemPrompt: `"Run: python skills/plan/scripts/validate_sdd_contracts.py 01-concepcao/sdd-[slug].md --bdd 01-concepcao/bdd-[slug].md until exit 0."`.
  Para que o subagente execute comandos em Python, a ferramenta `run_command` precisa estar habilitada. Isso confere ao subagente acesso total de execução de código no terminal do sistema operacional (PowerShell no Windows / Bash no Linux). Se o subagente sofrer injeção de prompt indireta (ex.: a partir de especificações em issues lidas no Step 1 ou docstrings maliciosas no repositório), ele pode executar comandos arbitrários no host, modificar arquivos fora de `01-concepcao/` (como `src/`, dotfiles ou `.git/hooks`), ou exfiltrar dados sensíveis.
- **Evidências da Mitigação Implementada:**
  1. **Implementado:** Revogação da ferramenta `run_command` de `bdd-architect` e `sdd-architect` em [`plan-goldfish.md:9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L9) e [`SKILL.md:16-17`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L16-L17).
  2. **Implementado:** A execução do script [`validate_sdd_contracts.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py) é realizada **exclusivamente pelo Orquestrador Principal** após a autoria do subagente ([`plan-goldfish.md:11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L11)).
  3. **Implementado:** Se a validação falhar, o Orquestrador repassa o erro cirúrgico via `send_message` mantendo o subagente isolado e sem privilégios de terminal ([`plan-goldfish.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L12)).
  4. **Implementado:** Permissões de escrita restritas estritamente ao diretório `01-concepcao/` ([`plan-goldfish.md:10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L10)).

---

### [PLAN-LLM06-02] Diretriz de Execução em Loop sem Circuit Breaker ("until exit 0") no `sdd-architect`
- **Categorias OWASP Associadas:** LLM06 (Unbounded Consumption) / ASI10 (Rogue Agents)
- **Severidade:** **Alta**
- **Status:** 🟢 **Totalmente Mitigado**
- **Localização Exata:** [`skills/plan/references/plan-goldfish.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L12).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**
  O SystemPrompt instrui o agente a rodar o validador `"until exit 0"`. Se o arquivo Markdown gerado contiver erros persistentes de validação (por exemplo, incompatibilidade sintática de rótulos Mermaid com espaços que o modelo não consegue corrigir, ou divergência insuperável de cenários com o BDD), o subagente entrará em loop infinito de execução e edição. Como este agente roda com `Model: "inherit"` (o modelo de mais alta capacidade e maior custo de tokens), a sessão consumirá tokens de forma exponencial até esgotar a cota ou atingir timeout, sem acionar um mecanismo de parada ou alarme humano.
- **Evidências da Mitigação Implementada:**
  **Implementado:** A diretiva perigosa `"until exit 0"` foi removida do SystemPrompt do `sdd-architect`. O Orquestrador Principal gerencia um circuit breaker estrito com `MaxIterations: 2` ([`plan-goldfish.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L12) e [`SKILL.md:17`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L17)). Caso a validação de contratos não atinja sucesso após 2 retries, a execução é interrompida e o relatório de erros é escalado para arbitragem humana via `ask_question`.

---

### [PLAN-ASI08-LLM10-03] Lacunas Semânticas no `validate_sdd_contracts.py`: Ausência de Validação de Tipos e Paridade Superficial de Exceções
- **Categorias OWASP Associadas:** ASI08 (Cascading Failures) / LLM10 (Improper Output Handling)
- **Severidade:** **Média**
- **Status:** 🟡 **Mitigado (integrado no fluxo CLI)**
- **Localização Exata:** [`skills/plan/scripts/validate_sdd_contracts.py#L117-L210`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py#L117-L210) e [`tests/skills/test_scanners.py#L1369-L1404`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L1369-L1404).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**
  A validação de paridade implementada no script possui duas lacunas críticas:
  1. **Falta de Checagem de Assinaturas de Tipos:** As funções `extract_sequence_called_methods` e `extract_class_declared_methods` extraem apenas os identificadores textuais dos métodos (`method_match.group(1)`). O script **não valida** se os tipos dos argumentos (ex.: `req: RequestDTO`) e os tipos de retorno conferem entre os dois diagramas, nem se conferem com os modelos de dados tipados (Pydantic/YAML).
  2. **Validação Superficial de Exceções BDD:** A função `check_bdd_sdd_error_parity` busca qualquer ocorrência de `alt/else` no diagrama de sequência e qualquer string correspondente a `*Error` ou `*Exception` no arquivo todo. Se o arquivo BDD definir três cenários de erro distintos (`@unhappy-path`, `@security`, `@concurrency`), mas o SDD implementar apenas uma exceção genérica e omitir os tratamentos de segurança e concorrência, o validador emite `exit 0`. Esse gap cascateia diretamente para a implementação TDD, gerando código que não trata falhas de segurança especificadas no BDD.
- **Evidências da Mitigação Implementada:**
  **Implementado (Integrado ao CLI):** Ambas as evoluções estruturais foram implementadas como funções utilitárias em [`skills/plan/scripts/validate_sdd_contracts.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py):
  1. `extract_class_method_signatures` (L117-154) e `validate_method_signature_types` (L157-173): extrai assinaturas completas com parâmetros e tipos de retorno do `classDiagram` e valida tipos explícitos contra parâmetros não tipados (`untyped`).
  2. `check_bijective_bdd_sdd_scenarios` (L175-210): analisa individualmente cada cenário BDD tagueado com `@unhappy-path`, `@security` ou `@concurrency`, extrai a exceção ou status code esperado (`*Error`, `*Exception`, 401, 403, 404, 409, 422, 500) e valida que ele existe de forma explícita no SDD e em ramos `alt/else` do `sequenceDiagram`.
  3. Cobertura de Testes: validado por testes unitários em [`tests/skills/test_scanners.py#L1369-L1404`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L1369-L1404) (`TestValidateSddSignaturesAndBijectiveParity`), cobrindo tipagem de métodos e correspondência bijetora de cenários negativos.
  4. **Integração no Pipeline:** `validate_sdd_content` agora invoca `extract_class_method_signatures`/`validate_method_signature_types` (sobre os `classDiagram`) e `check_bijective_bdd_sdd_scenarios` (quando há BDD via `--bdd` ou Gherkin embutido), acionadas na execução CLI do Orquestrador.

---

### [PLAN-ASI02-04] Risco de Injeção em Comandos Shell e Worktrees por Permissividade no Regex de Branch
- **Categorias OWASP Associadas:** ASI02 (Tool Misuse and Exploitation) / ASI05 (Unexpected Code Execution)
- **Severidade:** **Média**
- **Status:** 🟢 **Totalmente Mitigado**
- **Localização Exata:** [`skills/plan/scripts/validate_branch.py#L28-L30`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_branch.py#L28-L30) e [`skills/plan/references/plan-git.md#L9-L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-git.md#L9-L11).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**
  A expressão regular de validação original em `validate_branch.py` continha o quantificador permissivo `.+`, aceitando caracteres perigosos no sufixo de branch (espaços, caracteres de controle e caracteres de injeção de shell `&`, `;`, `|`, `` ` ``, `$`). Quando o protocolo em [`plan-git.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-git.md#L11) orienta a criação de worktrees através do comando `git worktree add -b feat/[slug] ../worktrees/[slug] develop`, um slug malicioso poderia quebrar a sintaxe do shell ou causar travamento/injeção no ambiente.
- **Evidências da Mitigação Implementada:**
  **Implementado:** O regex `VALID_BRANCH_REGEX` em [`validate_branch.py:28-30`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_branch.py#L28-L30) foi restringido para permitir estritamente caracteres alfanuméricos em minúsculas e hífens:
  ```python
  VALID_BRANCH_REGEX = re.compile(
      r"^(feature|feat|bugfix|fix|hotfix|refactor|chore|docs|style|test|release)/[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*$"
  )
  ```
  A mitigação foi validada pela suite de testes unitários em [`tests/skills/test_scanners.py:726-736`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L726-L736) (`TestValidateBranchSafetyRegex`), que atesta a rejeição estrita de branches com metacaracteres maliciosos (`feat/test;rm -rf`, `feat/branch&whoami`, `feat/test$(id)`).

---

### [PLAN-ASI07-05] Ausência de Schema Estruturado (JSON/Pydantic) na Comunicação do Conselho Goldfish
- **Categorias OWASP Associadas:** ASI07 (Insecure Inter-Agent Communication) / ASI09 (Human-Agent Trust Exploitation)
- **Severidade:** **Baixa**
- **Status:** 🟢 **Totalmente Mitigado**
- **Localização Exata:** [`skills/plan/references/plan-goldfish.md#L30-L47`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L30-L47) e [`skills/plan/SKILL.md#L18`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L18).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**
  Os subagentes do Conselho Goldfish comunicavam seus relatórios em markdown livre (`"Output: Bulleted list classified as [CRITICAL], [MODERATE], [LOW], or ZERO_FINDINGS"`). Na etapa de arbitragem, o Orquestrador precisava processar esse texto em linguagem natural para construir a matriz de arbitragem, o que podia causar quebra no parsing de pipes (`|`), ocultar apontamentos de segurança ou induzir decisões com dados corrompidos.
- **Evidências da Mitigação Implementada:**
  **Implementado:** O protocolo em [`plan-goldfish.md:30-47`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L30-L47) e [`SKILL.md:18`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L18) formalizou um schema JSON rígido e obrigatório para os 3 críticos (`goldfish-yagni`, `goldfish-adversary`, `goldfish-implementer`):
  ```json
  {
    "persona": "goldfish-adversary",
    "status": "FINDINGS_FOUND",
    "findings": [
      {
        "severity": "CRITICAL",
        "category": "CONCURRENCY",
        "description": "...",
        "suggested_mitigation": "..."
      }
    ]
  }
  ```
  O Orquestrador faz o parsing seguro com validação de esquema antes de renderizar a tabela na Matriz de Arbitragem para o desenvolvedor humano via `ask_question`.

---

### [PLAN-DOWNSTREAM-06] Falta de Campos de Segurança (RBAC, Rate-Limit, PII) no Template de Contratos SDD
- **Categorias OWASP Associadas:** LLM02 (Sensitive Information Disclosure) / ASI08 (Cascading Failures)
- **Severidade:** **Média**
- **Status:** 🟢 **Totalmente Mitigado**
- **Localização Exata:** [`skills/plan/resources/sdd-contract-template.yaml#L13-L19`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/sdd-contract-template.yaml#L13-L19) e [`skills/plan/resources/plan-template.md#L151-L160`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/plan-template.md#L151-L160).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**
  O modelo original de especificação de contratos em YAML e os DTOs em Python contemplavam apenas validações básicas de formato (`type: string`, `format: uuid`). Não havia seção ou atributos para definição de escopos de autorização (RBAC), classificação de dados/PII para mascaramento em logs, nem limites de taxa (*Rate Limiting*) ou idempotência, transferindo o risco de omissão desses controles para a Fase 2 (`/implement`).
- **Evidências da Mitigação Implementada:**
  **Implementado:** O template [`resources/sdd-contract-template.yaml:13-19`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/sdd-contract-template.yaml#L13-L19) e o template de especificação [`resources/plan-template.md:151-160`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/plan-template.md#L151-L160) foram expandidos com o bloco obrigatório `security:`:
  ```yaml
  security:
    authorization_scope: "{{REQUIRED_RBAC_ROLE_OR_SCOPE}}"
    rate_limit_tier: "{{RATE_LIMIT_TIER_EG_STANDARD_STRICT}}"
    idempotency_required: true
    sensitive_fields:
      - "{{FIELD_TO_REDACT_IN_LOGS}}"
  ```
  Isso garante que requisitos essenciais de segurança e proteção de PII sejam formalmente contratados já na concepção arquitetural.

---

## 5. Plano de Ação Priorizado para a Skill `/plan`

### Quick Wins (Baixo Esforço / Alto Impacto)
- [x] **Revogação de Execução de Shell em Subagentes:** `run_command: forbidden` configurado para `bdd-architect` e `sdd-architect` em [`skills/plan/references/plan-goldfish.md:9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L9) e [`skills/plan/SKILL.md:16-17`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L16-L17); execução de `validate_sdd_contracts.py` transferida unicamente para o Orquestrador Principal.
- [x] **Circuit Breaker no Validador de Contratos:** SystemPrompt de `sdd-architect` e pipeline do Orquestrador configurados com limite estrito de `MaxIterations: 2` com escalação via `ask_question` ([`skills/plan/references/plan-goldfish.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L12) e [`skills/plan/SKILL.md:17`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L17)).
- [x] **Endurecimento do Regex de Branch (`validate_branch.py`):** Regex alfanumérico e hífens estrito `^[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*$` implementado em [`skills/plan/scripts/validate_branch.py:28-30`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_branch.py#L28-L30) e coberto por testes em [`tests/skills/test_scanners.py:726-736`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L726-L736).
- [x] **Confinamento de Escrita:** Subagentes de autoria estritamente confinados a `01-concepcao/bdd-[slug].md` e `01-concepcao/sdd-[slug].md` ([`skills/plan/references/plan-goldfish.md:10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L10) e [`skills/plan/SKILL.md:16-17`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L16-L17)).
- [x] **Isolamento contra Indirect Prompt Injection:** Envelopamento das especificações em tags `<untrusted_spec>...</untrusted_spec>` com diretiva explícita de dados passivos para os subagentes do Conselho Goldfish ([`skills/plan/references/plan-goldfish.md:22`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L22) e [`skills/plan/SKILL.md:18`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L18)).

### Evoluções Estruturais (Scripts / Arquitetura de Subagentes)
- [x] **Validação Estrita de Assinaturas e Tipos no `validate_sdd_contracts.py`:** Implementadas funções `extract_class_method_signatures` e `validate_method_signature_types` em [`skills/plan/scripts/validate_sdd_contracts.py:117-173`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py#L117-L173) e testadas em [`tests/skills/test_scanners.py:1370-1386`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L1370-L1386), verificando tipos explícitos de parâmetros e retorno em métodos do `classDiagram`. **Integrado** em `validate_sdd_content()` e executado no CLI. *(Status: ?? Conclu?do)*.
- [x] **Validação Bijetora BDD $\leftrightarrow$ SDD de Cenários Negativos:** Implementada função `check_bijective_bdd_sdd_scenarios` em [`skills/plan/scripts/validate_sdd_contracts.py:175-210`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py#L175-L210) e testada em [`tests/skills/test_scanners.py:1387-1404`](file:///e:/Codigos/antigravity-agentic-workflows/tests/skills/test_scanners.py#L1387-L1404), validando que cada cenário `@unhappy-path`, `@security` e `@concurrency` possui correspondência bijetora 1:1 de exceção/status code no SDD. **Integrado** em `validate_sdd_content()` e executado no CLI. *(Status: ?? Conclu?do)*.
- [x] **Padronização JSON Schema para o Conselho Goldfish:** Estruturadas as saídas de `goldfish-yagni`, `goldfish-adversary` e `goldfish-implementer` em formato JSON padronizado com campos `persona`, `status` e `findings` tipados ([`skills/plan/references/plan-goldfish.md:30-47`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L30-L47) e [`skills/plan/SKILL.md:18`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L18)).
- [x] **Expansão de Metadados de Segurança nos Contratos SDD:** Atualizados [`skills/plan/resources/sdd-contract-template.yaml:13-19`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/sdd-contract-template.yaml#L13-L19) e [`skills/plan/resources/plan-template.md:151-160`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/plan-template.md#L151-L160) com o bloco obrigatório `security:` (RBAC, PII masking, rate-limiting e idempotência).
