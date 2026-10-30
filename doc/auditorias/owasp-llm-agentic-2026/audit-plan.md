<Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/plan`>
**Data da Auditoria:** 2026-10-30  
**Skill Auditada:** [`skills/plan/SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md)  
**Documentação Arquitetural:** [`doc/skills/plan/README.md`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/plan/README.md)  
**Modelo de Execução da Skill:** SDD 2.0 Elephant & Goldfish: Main Orchestrator + Subagentes de Autoria (`bdd-architect` e `sdd-architect`, `Model: "inherit"`) + Goldfish Council (3x `flash`, Read-Only)  
**Status Geral de Segurança Agentic:** 🟡 Atenção Moderada (com 1 Achado de Severidade Crítica em Privilégios/RCE)

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
1. **Perspectiva A (Meta-Agêntica):** A skill apresenta avanços notáveis de design com o Conselho Goldfish e validação determinística via scripts Python (`validate_sdd_contracts.py`). Contudo, identifica-se uma vulnerabilidade arquitetural severa: o subagente `sdd-architect` possui agência excessiva com `EnableWriteTools: true` e a instrução explícita de executar comandos shell (`run_command`) localmente no terminal (`"Run: python skills/plan/scripts/validate_sdd_contracts.py ... until exit 0"`). Isso concede capacidade potencial de Execução Remota de Código (RCE) e escrita arbitrária no sistema operacional para um subagente em uma fase estritamente conceitual.
2. **Perspectiva B (Código Downstream):** O `goldfish-adversary` é uma defesa pró-ativa de alto valor, identificando condições de corrida (TOCTOU) e ausência de tratamento de exceções antes do início do TDD. No entanto, o script `validate_sdd_contracts.py` valida apenas a presença de nomes de métodos, sem validar a paridade de tipos de parâmetros e retorno entre os diagramas de sequência e de classes, e sem validar a cobertura 1:1 de cada cenário `@unhappy-path` por uma exceção específica, o que pode transferir ambiguidades de tipo para o `/implement`.

---

## 2. Matriz de Conformidade: OWASP Top 10 for LLM Applications (2025/2026)

| Código | Categoria OWASP LLM (2025/2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **LLM01** | Prompt Injection (Direta, Indireta ou Multimodal) | **Alta** | **Context-Zero Firewall**: `bdd-architect`, `sdd-architect` e o Conselho Goldfish não recebem o histórico bruto do chat de alinhamento ([`plan-goldfish.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L7)). | `sdd-architect` inspeciona manifestos do repositório (`package.json`, `pyproject.toml`) e `bdd-[slug].md` ([`plan-goldfish.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L12)). Injeções indiretas em docstrings ou manifestos podem influenciar a geração de comandos de terminal ou contratos. | 🟡 Atenção Moderada |
| **LLM02** | Sensitive Information Disclosure | **Média** | Subagentes do Conselho Goldfish rodam em `flash` com `EnableWriteTools: false` e não possuem ferramentas de rede. | Contratos SDD e DTOs gerados via [`sdd-contract-template.yaml`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/sdd-contract-template.yaml) podem incorporar segredos fictícios (senhas, API keys mockadas) que são salvos no Vault e comitados no histórico do Git. | 🟡 Atenção Moderada |
| **LLM03** | Excessive Agency | **Crítica** | Conselho Goldfish é estritamente Read-Only (`EnableWriteTools: false`) ([`plan-goldfish.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L16)). | **VULNERABILIDADE:** Subagentes `bdd-architect` e `sdd-architect` operam com `Model: "inherit"` e `Write: true`, sem isolamento de diretório (*jail* em `01-concepcao/`). O `sdd-architect` tem permissão de execução de shell no host via `run_command` ([`plan-goldfish.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L12)). | 🔴 Risco Elevado |
| **LLM04** | Supply Chain Vulnerabilities | **Média** | Fase 1 não instala pacotes; a skill `/infra` é o gatekeeper de dependências do ecossistema. | O `sdd-architect` pode alucinar pacotes externos inexistentes (slopsquatting) ou bibliotecas abandonadas no diagrama de componentes, recomendando-os para uso nas Fases 2 e 3. | 🟢 Robusto com Pontos de Atenção |
| **LLM05** | Data and Model Poisoning | **Média** | O validador determinístico [`validate_sdd_contracts.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py) audita a estrutura formal dos artefatos. | Se um `bdd-[slug].md` contendo lógica de negócio corrompida for aprovado pelo humano no Gate 1, ele é ingerido pelo `sdd-architect` como verdade inquestionável. | 🟢 Conforme |
| **LLM06** | Unbounded Consumption | **Alta** | Subagentes do Conselho Goldfish usam `Model: "flash"`, minimizando o consumo de cota e tokens de contexto ([`plan-goldfish.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L16)). | A diretiva no SystemPrompt de `sdd-architect` para executar `validate_sdd_contracts.py` `"until exit 0"` ([`plan-goldfish.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L12)) não impõe um limite máximo de tentativas (`MaxIterations`), podendo gerar loops caros no modelo `inherit`. | 🟡 Atenção Moderada |
| **LLM07** | System Prompt Leakage / Misinformation | **Média** | Prompts de autoria e crítica são modulares, estáticos e versionados no repositório. | Falha de alucinação semântica: `validate_sdd_contracts.py` não valida tipos de dados em assinaturas; o subagente `goldfish-implementer` pode deixar passar assinaturas incompatíveis. | 🟢 Robusto com Pontos de Atenção |
| **LLM08** | Hidden Context Exposure | **Baixa** | Separação estrita de sessões (*Elephant & Goldfish*); cada subagente roda em `conversationId` isolado e recebe apenas os artefatos estritamente necessários. | Excelente implementação da arquitetura Context-Zero. Zero vazamento de contexto não intencional entre subagentes paralelos. | 🟢 Conforme |
| **LLM09** | Vector and Embedding Weaknesses | **Baixa** | Não utiliza bases vetoriais nem geração RAG por embeddings. | Não aplicável diretamente ao design desta skill. | 🟢 Conforme |
| **LLM10** | Improper Output Handling | **Média** | Validador de YAML utiliza `yaml.safe_load(content)` ([`validate_sdd_contracts.py:157`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py#L157)), prevenindo vulnerabilidades de desserialização insegura. | Validação de paridade de erros utiliza expressões regulares genéricas (`r"\b[A-Z][A-Za-z0-9_]*(?:Error|Exception)\b"`), aceitando correspondências superficiais sem garantir amarração semântica estrita. | 🟢 Robusto com Pontos de Atenção |

---

## 3. Matriz de Conformidade: OWASP Top 10 for Agentic Applications (2026)

| Código | Categoria OWASP Agentic (2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **ASI01** | Agent Goal Hijack | **Alta** | Entrevista Socrática obrigatória no Step 1 via `ask_question` ([`plan-debate.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-debate.md#L12)) e Propostas Arquiteturais limitadas a no máximo 3 opções ([`plan-debate.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-debate.md#L16)). | Textos de issues maliciosas ou especificações carregadas no Step 1 podem tentar forçar arquiteturas inseguras ou desativar proteções sem que o orquestrador perceba antes da aprovação da proposta. | 🟢 Robusto com Pontos de Atenção |
| **ASI02** | Tool Misuse and Exploitation | **Alta** | Scripts dedicados com validação de argumentos via `argparse` ([`validate_branch.py:93`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_branch.py#L93) e [`validate_sdd_contracts.py:291`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py#L291)). | Expressão regular de branch em [`validate_branch.py:27-30`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_branch.py#L27-L30) aceita caracteres perigosos no sufixo (`.+`), possibilitando injeção em comandos Git de handover (`git worktree add -b feat/[slug] ../worktrees/[slug] develop`). | 🟡 Atenção Moderada |
| **ASI03** | Identity and Privilege Abuse | **Crítica** | Conselho Goldfish não herda permissão de escrita (`EnableWriteTools: false`), garantindo que os críticos não modifiquem a especificação sob análise ([`plan-goldfish.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L16)). | **VULNERABILIDADE:** Subagentes `bdd-architect` e `sdd-architect` recebem o mesmo nível de permissão do usuário (`Model: "inherit"`, `Write: true`), incluindo acesso a ferramentas de terminal para rodar Python, violando o princípio do Menor Privilégio (*Least Privilege*). | 🔴 Risco Elevado |
| **ASI04** | Agentic Supply Chain Vulnerabilities | **Média** | Templates estruturados versionados localmente em `resources/` ([`plan-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/plan-template.md) e [`sdd-contract-template.yaml`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/sdd-contract-template.yaml)). | Atualizações no comportamento de raciocínio dos modelos subjacentes (`flash` e `inherit`) podem alterar o rigor das críticas do Conselho Goldfish sem aviso. | 🟢 Conforme |
| **ASI05** | Unexpected Code Execution (RCE) | **Crítica** | Invariante central: "Zero code in Phase 1" ([`SKILL.md:8`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L8)). Bloqueio estrito de código de produção na fase de planejamento. | **VULNERABILIDADE:** O SystemPrompt de `sdd-architect` concede e orienta a execução de comandos de terminal (`run_command`) no ambiente local ([`plan-goldfish.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L12)). Se comprometido, o subagente pode disparar qualquer comando PowerShell/Bash arbitrário. | 🔴 Risco Elevado |
| **ASI06** | Memory and Context Poisoning | **Alta** | **Conselho Goldfish (Step 5)** atua como barreira anti-envenenamento de premissas, atacando ativamente overengineering, vulnerabilidades de concorrência e contratos incompletos ([`plan-goldfish.md:20-22`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L20-L22)). | A arbitragem dos achados é feita com o desenvolvedor via `ask_question`. Se o humano rejeitar os avisos do `goldfish-adversary`, premissas vulneráveis persistem no Living DoD em `01-concepcao/dod-[slug].md`. | 🟢 Robusto com Pontos de Atenção |
| **ASI07** | Insecure Inter-Agent Communication | **Média** | Fluxo hierárquico bem definido: Orquestrador aciona subagentes de autoria sequencialmente e subagentes críticos em paralelo (Map-Reduce). | A troca de mensagens entre o Orquestrador e os subagentes ocorre através de strings não estruturadas em Markdown, sem esquemas formais de validação (JSON Schema) ou assinaturas de integridade. | 🟡 Atenção Moderada |
| **ASI08** | Cascading Failures** | **Alta** | Validação automatizada cruzada com `--bdd` no [`validate_sdd_contracts.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py#L114-L152) impede o fechamento do planejamento com BDD e SDD incompatíveis. | O validador ignora tipos de parâmetros e retorno em assinaturas; contratos com tipos incompatíveis são aceitos e quebram a fase subsequente de TDD ([`/implement`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/SKILL.md)). | 🟡 Atenção Moderada |
| **ASI09** | Human-Agent Trust Exploitation | **Alta** | Dois portões de arbitragem humana obrigatórios com `ask_question`: Gate 1 (aprovação do BDD) e Gate de Arbitragem (achados do Conselho Goldfish) ([`doc/skills/plan/README.md:27-28`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/plan/README.md#L27-L28)). | A chancela visual do Conselho Goldfish (`yagni: ZERO_FINDINGS`) pode levar o desenvolvedor humano à complacência, aprovando o SDD sem inspecionar os detalhes de persistência e segurança. | 🟢 Robusto com Pontos de Atenção |
| **ASI10** | Rogue Agents | **Alta** | Os 5 subagentes possuem papéis cirúrgicos delimitados por personas claras e focadas ([`plan-goldfish.md:11-22`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L11-L22)). | A execução autônoma do `sdd-architect` para atingir `exit 0` sem checkpoints intermediários de aprovação permite que ele tome decisões arquiteturais não supervisionadas durante as correções. | 🟡 Atenção Moderada |

---

## 4. Pontos Críticos de Atenção (Achados Forenses Detalhados)

### [PLAN-ASI03-ASI05-01] Permissão Excessiva de Escrita e Execução de Shell (`run_command`) no Subagente `sdd-architect`
- **Categorias OWASP Associadas:** ASI03 (Identity and Privilege Abuse) / ASI05 (Unexpected Code Execution) / LLM03 (Excessive Agency)
- **Severidade:** **Crítica**
- **Localização Exata:** [`skills/plan/references/plan-goldfish.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L12) e [`skills/plan/SKILL.md#L17`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L17).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**
  Na Fase 1, o princípio arquitetural fundamental é *"Zero code in Phase 1"* ([`SKILL.md:8`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/SKILL.md#L8)). Contudo, a especificação instrui que o subagente `sdd-architect` deve rodar com `Model: "inherit"`, `Write: true` e orienta em seu SystemPrompt: `"Run: python skills/plan/scripts/validate_sdd_contracts.py 01-concepcao/sdd-[slug].md --bdd 01-concepcao/bdd-[slug].md until exit 0."`.
  Para que o subagente execute comandos em Python, a ferramenta `run_command` precisa estar habilitada. Isso confere ao subagente acesso total de execução de código no terminal do sistema operacional (PowerShell no Windows / Bash no Linux). Se o subagente sofrer injeção de prompt indireta (ex.: a partir de especificações em issues lidas no Step 1 ou docstrings maliciosas no repositório), ele pode executar comandos arbitrários no host, modificar arquivos fora de `01-concepcao/` (como `src/`, dotfiles ou `.git/hooks`), ou exfiltrar dados sensíveis.
- **Recomendação Cirúrgica de Mitigação:**
  1. Revogar a ferramenta `run_command` dos subagentes de autoria (`bdd-architect` e `sdd-architect`).
  2. A execução do script [`validate_sdd_contracts.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py) deve ser realizada **exclusivamente pelo Orquestrador Principal** após a conclusão da autoria do subagente.
  3. Se a validação do script falhar, o Orquestrador submete o erro cirúrgico de volta ao `sdd-architect` via `send_message`, preservando o princípio do menor privilégio e eliminando o vetor de RCE no subagente.
  4. Restringir as permissões de escrita dos subagentes para permitir gravação única e exclusivamente no diretório `01-concepcao/`.

---

### [PLAN-LLM06-02] Diretriz de Execução em Loop sem Circuit Breaker ("until exit 0") no `sdd-architect`
- **Categorias OWASP Associadas:** LLM06 (Unbounded Consumption) / ASI10 (Rogue Agents)
- **Severidade:** **Alta**
- **Localização Exata:** [`skills/plan/references/plan-goldfish.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L12).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**
  O SystemPrompt instrui o agente a rodar o validador `"until exit 0"`. Se o arquivo Markdown gerado contiver erros persistentes de validação (por exemplo, incompatibilidade sintática de rótulos Mermaid com espaços que o modelo não consegue corrigir, ou divergência insuperável de cenários com o BDD), o subagente entrará em loop infinito de execução e edição. Como este agente roda com `Model: "inherit"` (o modelo de mais alta capacidade e maior custo de tokens), a sessão consumirá tokens de forma exponencial até esgotar a cota ou atingir timeout, sem acionar um mecanismo de parada ou alarme humano.
- **Recomendação Cirúrgica de Mitigação:**
  Substituir a instrução `"until exit 0"` por um limite explícito de tentativas: `"Execute at most 2 retry attempts. If validation does not pass on the second retry, return the validation error report to the Orchestrator for human arbitration."`.

---

### [PLAN-ASI08-LLM10-03] Lacunas Semânticas no `validate_sdd_contracts.py`: Ausência de Validação de Tipos e Paridade Superficial de Exceções
- **Categorias OWASP Associadas:** ASI08 (Cascading Failures) / LLM10 (Improper Output Handling)
- **Severidade:** **Média**
- **Localização Exata:** [`skills/plan/scripts/validate_sdd_contracts.py#L70-L152`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py#L70-L152).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**
  A validação de paridade implementada no script possui duas lacunas críticas:
  1. **Falta de Checagem de Assinaturas de Tipos:** As funções `extract_sequence_called_methods` e `extract_class_declared_methods` extraem apenas os identificadores textuais dos métodos (`method_match.group(1)`). O script **não valida** se os tipos dos argumentos (ex.: `req: RequestDTO`) e os tipos de retorno conferem entre os dois diagramas, nem se conferem com os modelos de dados tipados (Pydantic/YAML).
  2. **Validação Superficial de Exceções BDD:** A função `check_bdd_sdd_error_parity` busca qualquer ocorrência de `alt/else` no diagrama de sequência e qualquer string correspondente a `*Error` ou `*Exception` no arquivo todo. Se o arquivo BDD definir três cenários de erro distintos (`@unhappy-path`, `@security`, `@concurrency`), mas o SDD implementar apenas uma exceção genérica e omitir os tratamentos de segurança e concorrência, o validador emite `exit 0`. Esse gap cascateia diretamente para a implementação TDD, gerando código que não trata falhas de segurança especificadas no BDD.
- **Recomendação Cirúrgica de Mitigação:**
  Evoluir o script [`validate_sdd_contracts.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_sdd_contracts.py) para:
  1. Extrair e comparar a lista de tipos de parâmetros e retornos entre `classDiagram` e DTOs declarados.
  2. Realizar mapeamento bijetor (1:1): para cada cenário BDD tagueado com `@unhappy-path`, `@security` ou `@concurrency`, exigir uma exceção ou código de erro documentado no SDD e um bloco `alt/else` correspondente no `sequenceDiagram`.

---

### [PLAN-ASI02-04] Risco de Injeção em Comandos Shell e Worktrees por Permissividade no Regex de Branch
- **Categorias OWASP Associadas:** ASI02 (Tool Misuse and Exploitation) / ASI05 (Unexpected Code Execution)
- **Severidade:** **Média**
- **Localização Exata:** [`skills/plan/scripts/validate_branch.py#L27-L30`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_branch.py#L27-L30) e [`skills/plan/references/plan-git.md#L9-L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-git.md#L9-L11).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**
  A expressão regular de validação em `validate_branch.py` é:
  ```python
  VALID_BRANCH_REGEX = re.compile(
      r"^(feature|feat|bugfix|fix|hotfix|refactor|chore|docs|style|test|release)/.+$",
      re.IGNORECASE,
  )
  ```
  O quantificador `.+` aceita qualquer caractere após a barra prefixal, incluindo espaços, caracteres de controle, sequências de escape e caracteres de injeção de shell (`&`, `;`, `|`, `` ` ``, `$`). Quando o protocolo em [`plan-git.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-git.md#L11) orienta a criação de worktrees através do comando `git worktree add -b feat/[slug] ../worktrees/[slug] develop`, um slug malicioso pode quebrar a sintaxe do shell ou causar travamento do ambiente de desenvolvimento.
- **Recomendação Cirúrgica de Mitigação:**
  Restringir o regex de validação em `validate_branch.py` para caracteres estritamente alfanuméricos separados por hífens ou barras de subnível seguras:
  ```python
  VALID_BRANCH_REGEX = re.compile(
      r"^(feature|feat|bugfix|fix|hotfix|refactor|chore|docs|style|test|release)/[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*$",
      re.IGNORECASE,
  )
  ```

---

### [PLAN-ASI07-05] Ausência de Schema Estruturado (JSON/Pydantic) na Comunicação do Conselho Goldfish
- **Categorias OWASP Associadas:** ASI07 (Insecure Inter-Agent Communication) / ASI09 (Human-Agent Trust Exploitation)
- **Severidade:** **Baixa**
- **Localização Exata:** [`skills/plan/references/plan-goldfish.md#L20-L29`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L20-L29).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**
  Os subagentes do Conselho Goldfish comunicam seus relatórios em markdown livre (`"Output: Bulleted list classified as [CRITICAL], [MODERATE], [LOW], or ZERO_FINDINGS"`). Na etapa de arbitragem, o Orquestrador precisa processar esse texto em linguagem natural para construir a matriz: `| # | Persona | Severity | Finding | Action |`. Caso um subagente emita descrições longas, quebras de linha ou caracteres de pipe (`|`), o parsing heurístico do Orquestrador pode corromper a tabela de apresentação, ocultar apontamentos de segurança do `goldfish-adversary` ou induzir o desenvolvedor a tomar decisões com base em dados incompletos.
- **Recomendação Cirúrgica de Mitigação:**
  Padronizar a saída dos 3 subagentes Goldfish em formato JSON estruturado com esquema rígido:
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
  O Orquestrador faz o parsing seguro com validação de esquema antes de renderizar a tabela para o usuário.

---

### [PLAN-DOWNSTREAM-06] Falta de Campos de Segurança (RBAC, Rate-Limit, PII) no Template de Contratos SDD
- **Categorias OWASP Associadas:** LLM02 (Sensitive Information Disclosure) / ASI08 (Cascading Failures)
- **Severidade:** **Média**
- **Localização Exata:** [`skills/plan/resources/sdd-contract-template.yaml#L8-L50`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/sdd-contract-template.yaml#L8-L50) e [`skills/plan/resources/plan-template.md#L143-L157`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/plan-template.md#L143-L157).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**
  O modelo de especificação de contratos em YAML e os DTOs em Python contemplam validações básicas de formato (`type: string`, `format: uuid`, `min_length`). No entanto, não há seção ou atributos para definição de:
  - Escopos de autorização / Perfis de acesso requeridos (RBAC).
  - Classificação de dados e diretivas de mascaramento de dados sensíveis/PII em logs e tracebacks.
  - Limites de taxa de requisições (*Rate Limiting*) e cabeçalhos de segurança (Idempotency-Key).
  Ao omitir essas especificações durante a concepção arquitetural, a responsabilidade é empurrada para a Fase 2 (`/implement`), onde desenvolvedores ou agentes implementadores frequentemente ignoram esses controles não contratados.
- **Recomendação Cirúrgica de Mitigação:**
  Expandir [`sdd-contract-template.yaml`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/sdd-contract-template.yaml) para incluir uma seção obrigatória `security:` em cada contrato, contemplando `authorization_scope`, `rate_limit_tier` e `sensitive_fields` (para redação em logs).

---

## 5. Plano de Ação Priorizado para a Skill `/plan`

### Quick Wins (Baixo Esforço / Alto Impacto)
- [x] **Revogação de Execução de Shell em Subagentes:** Atualizar [`skills/plan/references/plan-goldfish.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md#L12) transferindo a execução de `validate_sdd_contracts.py` exclusivamente para o Orquestrador Principal, desabilitando `run_command` no subagente `sdd-architect`.
- [x] **Circuit Breaker no Validador de Contratos:** Limitar o SystemPrompt do `sdd-architect` para no máximo 2 tentativas de correção antes de escalar o problema para arbitragem humana, removendo o padrão descontrolado `"until exit 0"`.
- [x] **Endurecimento do Regex de Branch (`validate_branch.py`):** Modificar [`skills/plan/scripts/validate_branch.py:27-30`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/scripts/validate_branch.py#L27-L30) para exigir caracteres estritamente alfanuméricos com hífens (`^[a-z0-9]+(?:-[a-z0-9]+)*$`), bloqueando caracteres de injeção shell.
- [x] **Confinamento de Escrita:** Adicionar diretiva em [`plan-goldfish.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/references/plan-goldfish.md) proibindo estritamente a criação ou edição de arquivos fora da pasta `01-concepcao/`.

### Evoluções Estruturais (Scripts / Arquitetura de Subagentes)
- [ ] **Validação Estrita de Assinaturas e Tipos no `validate_sdd_contracts.py`:** Implementar validação sintática avançada comparando os tipos de parâmetros e retorno declarados no `classDiagram` com os contratos YAML/DTOs.
- [ ] **Validação Bijetora BDD $\leftrightarrow$ SDD de Cenários Negativos:** Atualizar `check_bdd_sdd_error_parity` para verificar que cada cenário `@unhappy-path`, `@security` e `@concurrency` possui uma exceção tipada e um bloco `alt/else` individualmente mapeados.
- [x] **Padronização JSON Schema para o Conselho Goldfish:** Estruturar as saídas de `goldfish-yagni`, `goldfish-adversary` e `goldfish-implementer` em formato JSON validado por Pydantic antes da montagem da Matriz de Arbitragem.
- [x] **Expansão de Metadados de Segurança nos Contratos SDD:** Atualizar [`resources/sdd-contract-template.yaml`](file:///e:/Codigos/antigravity-agentic-workflows/skills/plan/resources/sdd-contract-template.yaml) com requisitos explícitos de segurança (RBAC, PII masking, rate-limiting e headers de idempotência).
