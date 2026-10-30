<Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/obsidian`>
**Data da Auditoria:** 2026-10-30  
**Skill Auditada:** [`skills/obsidian/SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md)  
**Documentação Arquitetural:** [`doc/skills/obsidian/README.md`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md)  
**Modelo de Execução da Skill:** 100% Orquestrador Principal (Zero Subagentes para eliminar boot token overhead e reter contexto na sessão ativa)  
**Status Geral de Segurança Agentic:** 🟡 Atenção Moderada (Apresenta excelente modelagem conceitual de atomicidade e patches cirúrgicos, mas carrega alta vulnerabilidade a Envenenamento de Memória Persistente (ASI06 / LLM05), ausência de scripts determinísticos de validação de schemas e dependência exclusiva de salvaguardas contratuais no prompt para evitar sobrescritas e exclusões).

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

### Superfície de Ataque e Riscos Principais
- **Perspectiva Meta-Agêntica:**
  1. **Envenenamento de Memória Persistente (Memory & Context Poisoning - ASI06 / LLM05):** O Obsidian Vault é a **memória de longo prazo** compartilhada por todas as 12 skills do Antigravity. Como toda sessão nova de chat é instruída a ler o cofre no boot ([`prompts/gemini.md#L16`](file:///e:/Codigos/antigravity-agentic-workflows/prompts/gemini.md#L16)), qualquer nota corrompida ou maliciosamente adulterada em `00-core-rules/` ou `01-concepcao/` contamina permanentemente o contexto de trabalho de todas as fases subsequentes.
  2. **Ausência de Camada Programática de Proteção (Lacking Hard Enforcement):** A skill não possui pasta `scripts/` com validadores em Python. Regras vitais como *"Overwrites forbidden on existing notes"* e *"Never delete notes"* ([`SKILL.md#L10-L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L10-L11)) são meras instruções textuais em Markdown. Como o Orquestrador roda com ferramentas ativas de filesystem (`write_file`, `edit_file`, `run_command`), uma alucinação grave ou injeção de prompt pode acionar sobrescrita acidental ou deleção de notas.
- **Perspectiva de Código Downstream:**
  A integridade do software produzido depende diretamente da veracidade das regras expressas no Vault. Se uma especificação SDD ou Living DoD contiver links fantasmas, tipagem corrompida ou bypass de regras de segurança não detectados por linting, os códigos gerados nas fases de `/implement` e `/refactor` herdarão essas falhas estruturais, propagando vulnerabilidades silenciosas em cascata (ASI08).

---

## 2. Matriz de Conformidade: OWASP Top 10 for LLM Applications (2025/2026)

| Código | Categoria OWASP LLM (2025/2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **LLM01** | **Prompt Injection (Direta, Indireta ou Multimodal)** | **Alta** | Operações de busca filtram metadados específicos (`type`, `feature`) ([`README.md#L79`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L79)). | Se uma nota do Vault contiver texto malicioso proveniente de uma issue ou payload externo, ao ser lida no boot via `@obsidian`, ela se torna uma injeção de prompt persistente indireta. | 🔴 Risco |
| **LLM02** | **Sensitive Information Disclosure** | **Média** | O protocolo define templates estruturados ([`resources/note-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/resources/note-template.md)) focados em decisões de design e regras de negócio. | Logs de pivots técnicos (`pivots-*.md`) ou relatórios de auditoria podem capturar tokens, strings de conexão ou stack traces reais sem sanitização prévia. | 🟡 Atenção |
| **LLM03** | **Excessive Agency** | **Alta** | Invariante `Surgical Patch` proíbe `vault_write` em notas já existentes ([`SKILL.md#L10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L10)). | Execução no Orquestrador mantém ferramentas de escrita aberta sem restrição de escopo de diretório; o runtime não bloqueia fisicamente exclusões de arquivo (`rm`/`Remove-Item`). | 🔴 Risco |
| **LLM04** | **Supply Chain Vulnerabilities** | **Média** | Templates canônicos unificados em [`resources/note-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/resources/note-template.md). | Templates de ADR e regras de domínio não possuem seções obrigatórias para *Threat Modeling* ou impacto em segurança cibernética. | 🟡 Atenção |
| **LLM05** | **Data and Model Poisoning** | **Crítica** | Invariante `Immutability` impede exclusões e exige uso de `status: superseded` ([`SKILL.md#L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L11)). | Como o cofre é a base externa de RAG/contexto persistente, alterações deliberadas ou alucinadas em `00-core-rules/` envenenam o raciocínio de todos os prompts futuros. | 🔴 Risco |
| **LLM06** | **Unbounded Consumption** | **Média** | Execução sem subagentes elimina boot token overhead de 3.000 a 8.000 tokens por chamada ([`README.md#L26`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L26)). | Notas de Living DoD ou pivots com histórico cumulativo excessivo (`action: "append"`) podem crescer indefinidamente, inflando o consumo de contexto ao serem carregadas. | 🟡 Atenção |
| **LLM07** | **System Prompt Leakage / Misinformation** | **Média** | Esquemas estritos de frontmatter com tipos padronizados ([`references/obsidian-protocol.md#L19-L25`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L19-L25)). | Ausência de linter automático permite a geração de metadados inválidos ou links para notas inexistentes (alucinação de referências). | 🟡 Atenção |
| **LLM08** | **Hidden Context Exposure** | **Média** | A política de "One Chat Per Macro Phase" instrui o isolamento de sessões no chat ([`prompts/gemini.md#L36`](file:///e:/Codigos/antigravity-agentic-workflows/prompts/gemini.md#L36)). | Dados sensíveis armazenados inadvertidamente em notas do Vault são expostos a todos os futuros chats que executarem a inicialização com `@obsidian`. | 🟡 Atenção |
| **LLM09** | **Vector and Embedding Weaknesses** | **Alta** | Uso de queries estruturadas por metadados (`type: adr`, `feature: [slug]`) ([`README.md#L79`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L79)). | Notas malformadas que falham no parsing de frontmatter tornam-se invisíveis para buscas; vulnerabilidade a manipulação de relevância se busca vetorial for utilizada. | 🔴 Risco |
| **LLM10** | **Improper Output Handling** | **Alta** | `vault_patch` opera por alvos estruturados (`heading`, `frontmatter`) ([`references/obsidian-protocol.md#L26-L30`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L26-L30)). | Falta de sanitização de caracteres especiais ou quebras de linha em payloads JSON de `vault_patch` pode corromper os delimitadores `---` do YAML ou truncar seções de markdown. | 🔴 Risco |

---

## 3. Matriz de Conformidade: OWASP Top 10 for Agentic Applications (2026)

| Código | Categoria OWASP Agentic (2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **ASI01** | **Agent Goal Hijack** | **Alta** | O campo `feature` deve coincidir rigorosamente com a branch ativa ([`SKILL.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L12), [`README.md#L57`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L57)). | Adulteração do Living DoD (`dod-[slug].md`) ou de cenários BDD pode desviar completamente o objetivo das fases de implementação e testes. | 🔴 Risco |
| **ASI02** | **Tool Misuse and Exploitation** | **Alta** | Restrição de patch por cabeçalho/frontmatter com proibição expressa de sobrescrita ([`README.md#L54`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L54)). | Ferramentas como `vault_write` ou `write_file` não contam com interceptor em tempo de execução para barrar mutações de arquivos fora da pasta do cofre. | 🟡 Atenção |
| **ASI03** | **Identity and Privilege Abuse** | **Alta** | A skill foi mantida no Orquestrador Principal para evitar subagentes com permissões excessivas ou orfãs ([`README.md#L21-L29`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L21-L29)). | O Orquestrador Principal opera sem segregação de permissões de filesystem, compartilhando o mesmo nível de privilégio irrestrito com outras tarefas. | 🟡 Atenção |
| **ASI04** | **Agentic Supply Chain Vulnerabilities** | **Baixa** | Modelos padronizados internos em [`resources/note-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/resources/note-template.md) sem dependências externas. | Templates estáticos não evoluem dinamicamente caso novos requisitos regulatórios de segurança surjam. | 🟢 Conforme |
| **ASI05** | **Unexpected Code Execution (RCE)** | **Média** | A skill `/obsidian` não executa código; restringe-se a operações documentais e chamadas de API do cofre. | Blocos de código incluídos em notas (ex.: templates de fórmulas ou cálculos em `note-template.md#L84-L86`) podem ser executados cegamente por outras skills (`/implement`). | 🟡 Atenção |
| **ASI06** | **Memory and Context Poisoning** | **Crítica** | Rastreabilidade bidirecional via `backlinks` antes de modificar `00-core-rules/` ([`SKILL.md#L21`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L21)). | O Vault é o repositório de memória persistente entre chats; uma corrupção não auditada de nota permanece gravada indefinidamente, intoxicando o contexto de múltiplos agentes. | 🔴 Risco |
| **ASI07** | **Insecure Inter-Agent Communication** | **Alta** | Links canônicos `[[nota]]` formalizam as referências de comunicação entre artefatos ([`README.md#L108-L115`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L108-L115)). | A passagem de estado assíncrona entre agentes (ex.: Orquestrador do `/plan` grava DoD $\rightarrow$ Orquestrador do `/implement` consome) ocorre sem verificação de assinatura digital ou hash de integridade. | 🔴 Risco |
| **ASI08** | **Cascading Failures** | **Crítica** | Regra de Paridade ([`SKILL.md#L13`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L13)) exige que links resolvam em disco para garantir integridade. | Falha na validação de premissas em BDD/SDD propaga-se diretamente para a implementação em código, quebra de contratos de API e falha no gate de release. | 🔴 Risco |
| **ASI09** | **Human-Agent Trust Exploitation** | **Alta** | Notas de auditoria (`audit-*.md`) e Living DoD (`dod-*.md`) estruturados para leitura humana com tabelas e checkboxes ([`README.md#L114`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L114)). | Marcações fraudulentas ou precipitadas de caixas de seleção `[x]` no Living DoD induzem os desenvolvedores humanos a acreditar que os testes e gates foram cumpridos. | 🔴 Risco |
| **ASI10** | **Rogue Agents** | **Média** | O escopo é rigidamente atrelado à branch corrente via metadado `feature: [slug]` ([`README.md#L57`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L57)). | Não há barreira física que impeça um agente de editar notas de outra funcionalidade (`feature: outra-feature`) sem consentimento humano. | 🟡 Atenção |

---

## 4. Pontos Críticos de Atenção (Achados Forenses Detalhados)

### [OBS-ASI06-01] Envenenamento de Memória Persistente e Vetores de Context Poisoning
- **Categorias OWASP:** `ASI06: Memory and Context Poisoning` / `LLM05: Data and Model Poisoning` / `ASI01: Agent Goal Hijack`
- **Severidade:** `Crítica`
- **Localização Exata:** [`skills/obsidian/SKILL.md#L10-L13`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L10-L13), [`doc/skills/obsidian/README.md#L17`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L17) e [`prompts/gemini.md#L16`](file:///e:/Codigos/antigravity-agentic-workflows/prompts/gemini.md#L16)
- **Descrição Técnica do Risco (Vetor de Ataque):**
  No ecossistema Antigravity, o Obsidian Vault funciona como a **Single Source of Truth (SSOT)** e a memória durável externa que conecta todas as fases do ciclo de desenvolvimento. No início de toda interação, o agente é instruído a carregar o contexto do cofre:
  ```text
  2. Query and load relevant context from the Obsidian Vault via @obsidian.
  ```
  Se um invasor conseguir injetar instruções adversariais em uma nota canônica (seja através de uma pull request maliciosa, issue manipulada incorporada ao BDD, ou prompt injection que instrua o agente a criar/alterar um ADR), essas instruções tornam-se **memória viva permanente**.
  Em todos os chats subsequentes, quando o agente inicializar qualquer fluxo (`/plan`, `/implement`, `/refactor`, `/review`), o contexto envenenado será inserido no prompt de sistema como verdade absoluta. O agente poderá ignorar regras de isolamento arquitetural, alterar permissões de segurança ou bypassar testes de regressão, caracterizando um ataque devastador de *Memory & Context Poisoning*.
- **Recomendação Cirúrgica de Mitigação:**
  1. Estabelecer um mecanismo de verificação de integridade para diretórios críticos (`00-core-rules/`). Toda alteração em convenções e ADRs aceitos deve exigir confirmação explícita humana (*Human-in-the-Loop*).
  2. Implementar um validador de integridade e assinatura digital ou hash Git para os arquivos do Vault, impedindo que notas criadas fora de commits assinados ou revisados sejam incorporadas no boot do sistema.

---

### [OBS-ASI03-02] Execução 100% no Orquestrador com Salvaguardas Meramente Contratuais contra Sobrescritas e Exclusões
- **Categorias OWASP:** `ASI03: Identity and Privilege Abuse` / `LLM03: Excessive Agency` / `ASI02: Tool Misuse`
- **Severidade:** `Alta`
- **Localização Exata:** [`skills/obsidian/SKILL.md#L10-L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L10-L11) e [`doc/skills/obsidian/README.md#L21-L29`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L21-L29)
- **Descrição Técnica do Risco (Vetor de Ataque):**
  A documentação da skill justifica a escolha de executar 100% no Orquestrador Principal (Zero Subagents) para poupar tokens de boot (3.000 a 8.000 tokens) e manter o contexto acessível no chat. Contudo, essa conveniência acarreta uma consequência de segurança crítica: o Orquestrador Principal opera com privilégios plenos de terminal (`run_command`) e escrita no disco (`write_file`, `edit_file`).
  Os invariantes operacionais:
  ```markdown
  | Invariant | Operational Rule |
  | **Surgical Patch** | Use vault_patch. Overwrites forbidden on existing notes. |
  | **Immutability** | Never delete notes. Set status: superseded and supersedes: [[note]]. |
  ```
  são **meramente declarativos em Markdown**. Não existe nenhum middleware de software, script ou proxy de API que bloqueie fisicamente uma chamada de `write_file` ou comando shell destrutivo (`rm -rf 00-core-rules/`) caso o modelo sofra alucinação ou atenda a uma solicitação adversarial de usuário. A integridade de notas históricas fundamentais depende exclusivamente da obediência do modelo à diretriz de prompt.
- **Recomendação Cirúrgica de Mitigação:**
  Desenvolver um hook pré-execução ou script de validação de escrita (`skills/obsidian/scripts/vault_guard.py`) que audite as chamadas do sistema de arquivos. Qualquer tentativa de sobrescrever notas existentes sem usar `vault_patch` ou qualquer tentativa de deleção física de arquivos dentro do cofre deve ser interceptada e rejeitada determinística e programaticamente.

---

### [OBS-LLM10-03] Ausência de Validação Determinística de Esquemas e Injeção de Frontmatter em `vault_patch`
- **Categorias OWASP:** `LLM10: Improper Output Handling` / `ASI02: Tool Misuse` / `LLM07: System Prompt Leakage / Misinformation`
- **Severidade:** `Alta`
- **Localização Exata:** [`skills/obsidian/references/obsidian-protocol.md#L19-L30`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L19-L30) e [`skills/obsidian/SKILL.md#L22-L23`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L22-L23)
- **Descrição Técnica do Risco (Vetor de Ataque):**
  A skill especifica esquemas formais para cada tipo de nota (`adr`, `domain_rule`, `pivot`, `dod`) e estipula que modificações de metadados devem usar `targetType: "frontmatter"`. No entanto, a skill `/obsidian` **não possui nenhum script utilitário na pasta `scripts/`**.
  Diferente de outras skills do projeto (como `/review` e `/infra` que possuem scripts AST e linters), a skill `/obsidian` confia cegamente que o LLM formulará o payload JSON de `vault_patch` com delimitadores corretos, valores válidos para o enum `status` (`proposed`, `accepted`, `superseded`, etc.) e tipos padronizados.
  Se o LLM emitir um payload contendo quebras de linha incorretas, caracteres não sanitizados ou chaves de metadados adulteradas, o patch pode:
  1. Corromper os delimitadores `---` do YAML, inutilizando a nota para parsers e buscas indexadas.
  2. Injetar metadados com status fraudulentos (ex.: forjar `status: accepted` em um ADR rejeitado).
  3. Desalinhar o campo `feature` em relação à branch Git ativa, violando a rastreabilidade.
- **Recomendação Cirúrgica de Mitigação:**
  Criar um script de validação de esquemas de notas (`skills/obsidian/scripts/validate_vault_schemas.py`), integrando-o à suíte de testes contínuos (`tests/skills/test_scanners.py`). O script deve verificar com `PyYAML` se todas as notas do cofre possuem blocos de frontmatter válidos, se os tipos e status pertencem aos enums permitidos e se o slug da feature confere com a convenção de nomenclatura.

---

### [OBS-LLM09-04] Fraquezas de Indexação, Vector/Embedding Weaknesses e ReDoS em `search_query`
- **Categorias OWASP:** `LLM09: Vector and Embedding Weaknesses` / `LLM06: Unbounded Consumption` / `ASI02: Tool Misuse`
- **Severidade:** `Média`
- **Localização Exata:** [`skills/obsidian/SKILL.md#L21`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L21) e [`skills/obsidian/examples/obsidian-example.md#L9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/examples/obsidian-example.md#L9)
- **Descrição Técnica do Risco (Vetor de Ataque):**
  A etapa 1 (*Index*) instrui o agente a executar `search_query` com filtros de metadados ou termos livres. Há duas vulnerabilidades estruturais:
  1. **Injeção de Query e ReDoS:** Se a ferramenta subjacente de busca aceitar expressões regulares ou operadores avançados sem sanitização prévia, queries complexas geradas a partir de insumos não confiáveis podem causar travamento por catastrofismo de backtracking (ReDoS) na indexação do cofre.
  2. **Manipulação de Relevância Vetorial / Lexical:** Se notas maliciosas ou rascunhos acumularem repetições artificiais de palavras-chave ou tags como `core`, `conventions` e `architecture`, essas notas capturarão o topo dos rankings de busca, fazendo com que o agente ignore a convenção oficial e baseie suas decisões nas notas manipuladas.
- **Recomendação Cirúrgica de Mitigação:**
  Adicionar diretrizes e sanitizadores estritos para argumentos da ferramenta `search_query`, garantindo que filtros de metadados utilizem dicionários tipados e sintaxe exata, e implementar limitação de resultados (*Top-K truncation*) com validação de precedência para caminhos canônicos (`00-core-rules/` sempre tem precedência sobre `01-concepcao/`).

---

### [OBS-ASI08-05] Proliferação de Links Fantasmas e Quebra de Rastreabilidade no Grafo de Conhecimento
- **Categorias OWASP:** `ASI08: Cascading Failures` / `LLM07: System Prompt Leakage / Misinformation`
- **Severidade:** `Média`
- **Localização Exata:** [`skills/obsidian/SKILL.md#L13`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L13), [`skills/obsidian/SKILL.md#L24`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L24) e [`doc/skills/obsidian/README.md#L108-L115`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L108-L115)
- **Descrição Técnica do Risco (Vetor de Ataque):**
  O Invariante de Paridade declara: *"Links must resolve to disk (00-core-rules/, 01-concepcao/, etc.)"*. No entanto, durante o fluxo criativo de concepção e especificação de software, modelos de linguagem frequentemente geram referências cruzadas a documentos hipotéticos ou ainda não redigidos (ex.: `[[adr-0025-token-revocation]]` ou `[[sdd-auth-refresh]]`).
  Sem um validador automatizado pós-escrita, esses **links fantasmas (*orphan/broken wikilinks*)** são persistidos no cofre. Quando habilidades downstream como `/implement` ou `/review` tentam carregar esses links como premissas de verdade contratual, deparam-se com arquivos inexistentes, forçando o modelo a alucinar os detalhes do contrato ou paralisar o pipeline de engenharia com falhas em cascata.
- **Recomendação Cirúrgica de Mitigação:**
  Implementar um verificador de integridade referencial de links (`skills/obsidian/scripts/check_vault_links.py`) que inspecione todos os `[[wikilinks]]` contidos nas notas modificadas e valide se o arquivo alvo existe fisicamente no disco. Se o link apontar para uma nota inexistente, a operação de salvamento deve exigir que a nota seja criada ou que o link seja sinalizado como pendente.

---

### [OBS-ASI09-06] Superfície de Exploração de Confiança em Checklists de Living DoD e Logs de Auditoria
- **Categorias OWASP:** `ASI09: Human-Agent Trust Exploitation` / `ASI01: Agent Goal Hijack`
- **Severidade:** `Média`
- **Localização Exata:** [`skills/obsidian/references/obsidian-protocol.md#L24`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L24) e [`doc/skills/obsidian/README.md#L114`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/obsidian/README.md#L114)
- **Descrição Técnica do Risco (Vetor de Ataque):**
  O Living DoD (`01-concepcao/dod-[slug].md`) é o documento que atesta para a equipe de engenharia se uma funcionalidade está pronta para release. Através de `vault_patch`, o agente pode atualizar cabeçalhos e marcar checkboxes como cumpridos: `- [x] Unit tests passing with 100% coverage`.
  Se um agente autônomo marcar uma tarefa como concluída sem que a suíte de testes tenha de fato rodado e passado com sucesso (alucinação de conformidade ou complacência do agente), desenvolvedores humanos e auditores confiarão no relatório visual gerado no cofre, promovendo código defeituoso ou vulnerável diretamente para staging ou produção.
- **Recomendação Cirúrgica de Mitigação:**
  Estabelecer uma regra estrita de comprovação empírica em [`obsidian-protocol.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md): qualquer patch que altere checkboxes de Living DoD (`- [ ]` para `- [x]`) deve obrigatoriamente referenciar e anexar o identificador do commit, a saída de execução de testes ou o log de auditoria comprovatório.

---

## 5. Plano de Ação Priorizado para a Skill `/obsidian`

### Quick Wins (Baixo Esforço / Alto Impacto)
- [x] **Enriquecimento dos Templates de Nota:** Atualizar [`skills/obsidian/resources/note-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/resources/note-template.md) para incluir campos explícitos de segurança cibernética nos templates de ADR (seção `## Security & Threat Considerations`) e regras de domínio (seção `## Security Invariants & Access Controls`).
- [x] **Guardrail Explícito de Não-Deleção:** Reforçar a regra no SystemPrompt de [`skills/obsidian/SKILL.md#L10-L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/SKILL.md#L10-L11) estabelecendo que comandos de terminal de remoção (`rm`, `del`, `git rm`) e sobrescritas diretas via `write_file` no diretório do cofre são estritamente proibidos e constituem violação de protocolo.
- [x] **Regra de Comprovação de Checklists no Living DoD:** Adicionar em [`skills/obsidian/references/obsidian-protocol.md#L28`](file:///e:/Codigos/antigravity-agentic-workflows/skills/obsidian/references/obsidian-protocol.md#L28) a obrigatoriedade de vincular evidência documental (saída de teste ou hash de commit) ao marcar itens como concluídos.

### Evoluções Estruturais (Scripts / Arquitetura de Subagentes)
- [x] **Criação do Script de Linter de Frontmatter (`validate_vault_schemas.py`):** Criar `skills/obsidian/scripts/validate_vault_schemas.py` para validar via AST/PyYAML a conformidade de todas as notas contra os esquemas da tabela de metadados (tipos, campos obrigatórios, status permitidos).
- [x] **Criação do Validador de Integridade de Grafo (`check_vault_links.py`):** Desenvolver script Python em `skills/obsidian/scripts/` para percorrer os wikilinks `[[nota]]` em todas as notas do Vault, garantindo que não existam links quebrados ou referências a artefatos não existentes.
- [ ] **Mecanismo de Proteção e Assinatura para `00-core-rules/`:** Desenvolver guardrail determinístico que exija aprovação explícita (*Human-in-the-Loop*) antes de aplicar patches em convenções centrais e regras de arquitetura.
</Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/obsidian`>
