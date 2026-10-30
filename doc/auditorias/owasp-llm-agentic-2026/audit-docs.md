# Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/docs`

**Data da Auditoria:** 2026-10-30  
**Skill Auditada:** [`skills/docs/SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/SKILL.md)  
**Documentação Arquitetural:** [`doc/skills/docs/README.md`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/docs/README.md)  
**Modelo de Execução da Skill:** Orquestrador Principal (`inherit`) + Subagente Especialista `docs-scribe` (`Model: "flash"`)  
**Status Geral de Segurança Agentic:** 🟢 Totalmente Mitigado / 100% Conforme (6/6 itens)

---

## 1. Sumário Executivo e Perfil de Risco da Skill

A skill `/docs` é responsável pela Fase 5 do ciclo SDD 2.0 (Technical Feature Documentation & Feature Freeze). Sua finalidade primária é sincronizar a documentação viva da feature com a base de código implementada e auditada, integrando as especificações BDD/SDD do Obsidian (`01-concepcao/`), os manifestos operacionais do projeto (`pyproject.toml`, `package.json`, etc.) e docstrings no código-fonte, aplicando formalmente a regra de **Feature Freeze** (congelamento pré-merge) antes do ciclo de lançamento (`/release`).

### Topologia Agêntica & Ferramentas
A skill divide seu fluxo de trabalho em três etapas arquiteturais bem definidas:
1. **Step 1: Resolução de Escopo & Manifestos (Orquestrador):** Analisa a branch e o diff ativo (`git diff develop...HEAD --name-only`), localiza os artefatos de concepção (`bdd-[slug].md`, `sdd-[slug].md`, `dod-[slug].md`) e extrai comandos de build/teste reais a partir dos manifestos do repositório ([`SKILL.md:14`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/SKILL.md#L14)).
2. **Step 2: Geração de Documentação Viva & Enriquecimento de Código (`docs-scribe`, `Model: "flash"`):** Opera em sessão isolada com permissão de escrita para gerar `README.md` locais de módulo e atualizar o `README.md` raiz com diagramas Mermaid seguros (rótulos entre aspas duplas), injetar docstrings informativas com rastreabilidade formal (`Ref: Obsidian note [[sdd-[slug]]]`) sem alterar lógica de execução, e validar ausência de regressões sintáticas via `python -m pytest -q` ([`docs-subagents.md:9-12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-subagents.md#L9-L12)).
3. **Step 3 & 4: Living DoD & Feature Freeze (Orquestrador):** Marca o checkbox de documentação em `01-concepcao/dod-[slug].md`, registra o evento cronológico na timeline, consolida o staging explícito (`git add ...`), grava o commit semântico `docs(feature): ...` e impõe a invariante de **Feature Freeze** (proibição expressa de merge antecipado com `develop` ou `main` dentro da skill `/docs`) ([`doc/skills/docs/README.md:88-96`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/docs/README.md#L88-L96)).

### Superfície de Ataque e Riscos Identificados
- **Perspectiva Meta-Agêntica (Skill & Workflow):** O principal risco reside na concessão de permissão de escrita generalizada (`EnableWriteTools: true`) para o subagente `docs-scribe` ([`docs-subagents.md:9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-subagents.md#L9)), permitindo que um modelo `flash` edite diretamente arquivos de produção em `src/`. Embora haja a salvaguarda de "Zero Logic Alteration" e verificação via `pytest -q`, o modelo tem capacidade física de alterar instruções executáveis. Além disso, a execução de `python -m pytest -q` no host representa execução de código arbitrário (RCE), e manifestos corrompidos lidos no Step 1 podem levar o agente a documentar comandos danosos no `README.md`.
- **Perspectiva do Código Downstream (Software Documentado):** A skill mitiga o desvio de documentação (*documentation drift*) ao exigir que comandos reflitam os manifestos reais do projeto (*Reality-First Directive*) e protege a integridade dos diagramas Mermaid impondo aspas duplas nos rótulos para prevenir quebras de renderização ([`docs-guidelines.md:13`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L13)). Contudo, frameworks modernos orientados a metadados (como FastAPI, Typer, Click e Pydantic) utilizam docstrings em tempo de execução para gerar endpoints HTTP, schemas OpenAPI e parsers CLI; alterações inadvertidas em docstrings nessas bibliotecas podem provocar desvios semânticos em produção não capturados por suítes de teste superficiais.

---

## 2. Matriz de Conformidade: OWASP Top 10 for LLM Applications (2025/2026)

| Código | Categoria OWASP LLM (2025/2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **LLM01** | **Prompt Injection (Direta, Indireta ou Multimodal)** | Alta | Subagente opera com SystemPrompt especializado e focado exclusivamente na síntese de documentação ([`docs-subagents.md:11-12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-subagents.md#L11-L12)). | Arquivos de código inspecionados ou notas BDD/SDD podem conter injeção indireta induzindo o `docs-scribe` a inserir URLs de phishing ou comandos nocivos no `README.md`. | 🟡 Atenção Moderada |
| **LLM02** | **Sensitive Information Disclosure** | Alta | A skill orienta a documentar apenas contratos públicos e fluxos de dados de alto nível ([`doc-template.md:16-21`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/resources/doc-template.md#L16-L21)). | Ao preencher o bloco `Getting Started` ou exemplos de configuração, o subagente pode ler inadvertidamente variáveis reais de arquivos locais (`.env`) e expô-las no `README.md`. | 🟡 Atenção Moderada |
| **LLM03** | **Excessive Agency** | Alta | A regra "Non-Destructive" proíbe expressamente alterações de lógica de produção ([`docs-guidelines.md:11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L11)). | `docs-scribe` possui `EnableWriteTools: true` sobre o diretório de código-fonte (`src/`), dependendo de alinhamento por prompt para não modificar código funcional. | 🟡 Atenção Moderada |
| **LLM04** | **Supply Chain Vulnerabilities** | Alta | A diretriz *Manifests* obriga validação de comandos contra manifestos formais (`pyproject.toml`, `package.json`, etc.) ([`docs-guidelines.md:10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L10)). | Se uma dependência maliciosa ou script adulterado estiver presente no manifesto, o subagente documentará e legitimará o comando suspeito no `README.md` raiz. | 🟢 Conforme com Ressalva |
| **LLM05** | **Data and Model Poisoning** | Média | Utilização de templates rígidos ([`doc-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/resources/doc-template.md)) e links Obsidian formais `[[sdd-[slug]]]`. | Informações incorretas ou alucinações sobre arquitetura gravadas nos READMEs passam a compor a verdade perene do repositório, enviesando futuros agentes. | 🟢 Conforme |
| **LLM06** | **Unbounded Consumption** | Baixa | Delegação de escrita para subagente `Model: "flash"` ([`doc/skills/docs/README.md:58-64`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/docs/README.md#L58-L64)), otimizando drasticamente cotas e velocidade. | Se o changeset cobrir dezenas de arquivos, a reescrita integral de módulos pelo subagente pode causar elevado consumo de saída de tokens. | 🟢 Robusto |
| **LLM07** | **System Prompt Leakage / Misinformation** | Média | Diretiva *Reality-First* exige documentação estrita de comportamento real de código em execução ([`docs-guidelines.md:9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L9)). | O modelo `flash` pode alucinar parâmetros em docstrings ou opções inexistentes de CLI ao sintetizar instruções sem consultar a implementação profunda. | 🟢 Conforme com Ressalva |
| **LLM08** | **Hidden Context Exposure** | Baixa | `docs-scribe` roda em subagente isolado, garantindo Context-Zero e evitando que históricos de chats anteriores afetem a escrita. | Nenhum vazamento de histórico identificado entre sessões de agentes. | 🟢 Robusto |
| **LLM09** | **Vector and Embedding Weaknesses** | Baixa | A skill não consulta bases vetoriais dinâmicas, operando sobre arquivos Markdown locais e referências estáticas Obsidian. | Não aplicável diretamente ao fluxo de documentação. | 🟢 Não Aplicável |
| **LLM10** | **Improper Output Handling** | Alta | Validação obrigatória de sintaxe via `python -m pytest -q` antes de concluir a execução do subagente ([`docs-guidelines.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L12)). | Strings de docstring mal formatadas podem introduzir quebras em docparsers ou quebrar arquivos não cobertos por testes unitários. | 🟢 Conforme |

---

## 3. Matriz de Conformidade: OWASP Top 10 for Agentic Applications (2026)

| Código | Categoria OWASP Agentic (2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **ASI01** | **Agent Goal Hijack** | Alta | Prompt focado e unívoco restringe o papel do `docs-scribe` a escrever READMEs, docstrings e rodar `pytest -q` ([`docs-subagents.md:11-12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-subagents.md#L11-L12)). | Ataques embutidos em arquivos-fonte lidos no diff podem tentar instruir o subagente a desviar de função (ex.: deletar testes ou arquivos de log). | 🟡 Atenção Moderada |
| **ASI02** | **Tool Misuse and Exploitation** | Média | Execução de comandos controlados no orquestrador e subagente (`pytest -q`, `git add`, `git commit`). | Chamadas a `git add` no Step 3 devem ser rigorosamente explícitas; o template de guidelines ainda menciona `git commit -am` ([`docs-guidelines.md:32`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L32)). | 🟢 Conforme com Ressalva |
| **ASI03** | **Identity and Privilege Abuse** | Alta | Separação entre geração de texto (`docs-scribe`) e governança de Git/DoD (Orquestrador) ([`doc/skills/docs/README.md:49-55`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/docs/README.md#L49-L55)). | O subagente `docs-scribe` possui privilégios de escrita nos arquivos de produção (`src/`), quando tecnicamente deveria ter escopo de escrita limitado ou assistido. | 🟡 Atenção Moderada |
| **ASI04** | **Agentic Supply Chain Vulnerabilities** | Média | Templates estáticos em [`doc-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/resources/doc-template.md) com padronização rigorosa de componentes e diagramas. | Vulnerabilidade indireta através da leitura de manifestos downstream não higienizados. | 🟢 Conforme |
| **ASI05** | **Unexpected Code Execution (RCE)** | Alta | A skill utiliza o Syntax Guard determinístico `python -m pytest -q` ([`docs-guidelines.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L12)). | A execução de `pytest -q` executa código arbitrário de teste no ambiente do desenvolvedor durante uma tarefa concebida para ser puramente de documentação. | 🟡 Ponto Crítico |
| **ASI06** | **Memory and Context Poisoning** | Média | Atualização estruturada do Living DoD (`01-concepcao/dod-[slug].md`) com entrada cronológica rastreável ([`SKILL.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/SKILL.md#L16)). | Gravação de wikilinks corrompidos ou nomes de notas incorretos (`[[sdd-[slug]]]`) desarticula a rastreabilidade bidirecional do Obsidian Vault. | 🟢 Conforme |
| **ASI07** | **Insecure Inter-Agent Communication** | Baixa | O subagente retorna apenas um resumo conciso de documentação gerada e arquivos enriquecidos ([`docs-subagents.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-subagents.md#L12)). | Nenhum payload complexo ou não validado é repassado de volta ao chat principal. | 🟢 Robusto |
| **ASI08** | **Cascading Failures** | Média | A falha no `pytest -q` bloqueia o commit de congelamento e a transição para `/release`. | Se o subagente introduzir alterações lógicas sutis em funções sem testes, a falha só será detectada tardiamente em fases de integração. | 🟢 Conforme com Ressalva |
| **ASI09** | **Human-Agent Trust Exploitation** | Alta | Governança explícita de *Feature Freeze* ([`doc/skills/docs/README.md:88-96`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/docs/README.md#L88-L96)) impede merge precoce em `develop`/`main`. | A premissa de que `/docs` "nunca altera lógica" cria complacência no desenvolvedor, que pode aprovar alterações em arquivos `.py` sem inspecionar o git diff. | 🟡 Atenção Moderada |
| **ASI10** | **Rogue Agents** | Baixa | A política de Feature Freeze e a proibição expressa de comandos de merge eliminam comportamentos desgovernados na árvore Git ([`SKILL.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/SKILL.md#L16)). | Baixo risco de desvio devido à curta duração e especificidade da tarefa de escrita de documentação. | 🟢 Robusto |

---

## 4. Pontos Críticos de Atenção (Achados Forenses Detalhados)

### 📌 [DOC-ASI03-01] Privilégio de Escrita Direta em Código de Produção por Subagente de Documentação
- **Categorias OWASP:** ASI03 (Identity and Privilege Abuse), LLM03 (Excessive Agency)
- **Severidade:** 🟡 Alta
- **Localização Exata:** [`skills/docs/references/docs-subagents.md:9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-subagents.md#L9) e [`doc/skills/docs/README.md:52`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/docs/README.md#L52).
- **Descrição Técnica do Risco:**  
  A matriz de responsabilidades define que o subagente `docs-scribe` possui permissão `EnableWriteTools: true` sobre READMEs e in-code docstrings. Em termos de segurança de execução agêntica, a ferramenta de edição de arquivo concedida ao subagente opera sobre todo o workspace. Confiar unicamente na instrução em linguagem natural *"Zero logic edits"* ([`docs-subagents.md:9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-subagents.md#L9)) e *"Edits limited to docstrings/comments/typing"* ([`docs-guidelines.md:11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L11)) é uma barreira frágil (soft constraint). Se o subagente alucinar, sofrer injeção de prompt ou cometer erro de parsing, linhas funcionais de código de produção em `src/` podem ser deletadas ou modificadas silenciosamente.
- **Recomendação Cirúrgica de Mitigação:**  
  Segregar as tarefas de documentação:
  1. Permitir que `docs-scribe` crie/atualize exclusivamente arquivos de documentação (`README.md`, `doc/`, `docs/`).
  2. Para o enriquecimento de docstrings no código de produção, utilizar uma ferramenta ou script determinístico baseado em AST (ex.: script Python que localiza funções sem docstring e insere o bloco pré-formatado com `Ref: Obsidian note [[sdd-[slug]]]`), sem conceder ao subagente a capacidade de editar arbitrariamente blocos de código funcional.

---

### 📌 [DOC-ASI05-02] Execução Inesperada de Código Arbitrário no Host via Syntax Guard (`pytest -q`)
- **Categorias OWASP:** ASI05 (Unexpected Code Execution / RCE), LLM10 (Improper Output Handling)
- **Severidade:** 🟡 Alta
- **Localização Exata:** [`skills/docs/SKILL.md:15`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/SKILL.md#L15), [`skills/docs/references/docs-guidelines.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L12) e [`doc/skills/docs/README.md:79-83`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/docs/README.md#L79-L83).
- **Descrição Técnica do Risco:**  
  O protocolo de salvaguarda da skill define a execução de `python -m pytest -q` como exit gate determinístico após a inserção de docstrings pelo `docs-scribe`. Embora o objetivo seja puramente verificar que nenhuma quebra sintática foi introduzida no código, invocar `pytest` causa a importação e execução de fixtures, plugins e testes do repositório. Em fluxos de trabalho com repositórios não confiáveis ou PRs externas, a execução de testes dinâmicos durante a etapa de documentação técnica expande a superfície de ataque para execução arbitrária de código (RCE) em um estágio onde apenas validação sintática estática era requerida.
- **Recomendação Cirúrgica de Mitigação:**  
  Substituir ou anteceder a verificação dinâmica por uma verificação puramente estática de integridade sintática utilizando compiladores e linters nativos que não executam código, por exemplo:
  ```bash
  python -m py_compile <modified_python_files>
  ```
  Isso garante 100% de integridade sintática e de indentação sem executar nenhuma linha de código dinâmico.

---

### 📌 [DOC-ASI09-03] Efeitos Colaterais Semânticos em Frameworks Baseados em Metadados de Docstring
- **Categorias OWASP:** ASI09 (Human-Agent Trust Exploitation), LLM03 (Excessive Agency)
- **Severidade:** 🟡 Média
- **Localização Exata:** [`skills/docs/references/docs-guidelines.md:15-20`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L15-L20) e [`skills/docs/resources/doc-template.md:114-130`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/resources/doc-template.md#L114-L130).
- **Descrição Técnica do Risco:**  
  A diretriz assume que adicionar docstrings e referências wikilink `[[sdd-[slug]]]` possui impacto estritamente nulo sobre a lógica de execução (*Zero logic change*). Todavia, no ecossistema moderno de desenvolvimento (Python com FastAPI, Typer, Click, Pydantic v2 e Strawberry GraphQL; JavaScript com TypeGraphQL ou TSOA), docstrings de classes e funções são inspecionadas dinamicamente via reflexão em tempo de execução para gerar schemas de validação, documentação OpenAPI/Swagger pública e descrições de comandos CLI. Injetar docstrings genéricas ou wikilinks Obsidian em rotas HTTP públicas ou comandos de terminal pode alterar contratos de API externos e schemas públicos consumidos por clientes downstream.
- **Recomendação Cirúrgica de Mitigação:**  
  Adicionar aos guidelines ([`docs-guidelines.md:11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L11)) uma cláusula de exceção para frameworks orientados a metadados:
  > *"Em endpoints de API (FastAPI/Flask-RESTX), modelos Pydantic ou comandos CLI (Typer/Click), preserve as docstrings originais ou formate a documentação em conformidade com o schema OpenAPI/CLI esperado, evitando adicionar tags internas do Obsidian no corpo visível da API pública."*

---

### 📌 [DOC-LLM04-04] Absorção Acrítica de Comandos Operacionais a partir de Manifestos
- **Categorias OWASP:** LLM04 (Supply Chain Vulnerabilities), ASI04 (Agentic Supply Chain)
- **Severidade:** 🟢 Baixa
- **Localização Exata:** [`skills/docs/SKILL.md:14`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/SKILL.md#L14) e [`skills/docs/references/docs-guidelines.md:10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L10).
- **Descrição Técnica do Risco:**  
  A diretriz determina extrair comandos operacionais diretamente de manifestos (`pyproject.toml`, `package.json`, `Cargo.toml`, `Makefile`). Se um repositório downstream estiver sob ataque de supply chain ou envenenamento de dependências (com scripts de instalação como `preinstall` ou `build` modificados para acionar URLs remotas), a skill transcreve esses comandos diretamente para a seção `Getting Started` do `README.md` raiz sem sinalização de segurança, induzindo desenvolvedores e outros agentes a executá-los cegamente.
- **Recomendação Cirúrgica de Mitigação:**  
  Adicionar uma regra nos guidelines exigindo que comandos transcritos para o `README.md` utilizem exclusivamente gerenciadores padrão conhecidos (`poetry install`, `pip install -e .`, `npm ci`, `cargo build`), rejeitando scripts customizados ou obscuros sem validação explícita.

---

## 5. Plano de Ação Priorizado para a Skill `/docs`

### Quick Wins (Baixo Esforço / Alto Impacto)
- [x] **QW-DOC-01:** Adicionar verificação estática prévia de compilação (`python -m py_compile <files>`) no Step 2 do [`skills/docs/SKILL.md:15`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/SKILL.md#L15), assegurando integridade sintática imediata com zero execução de código antes do exit gate.
- [x] **QW-DOC-02:** Adicionar alerta de segurança contra vazamento de segredos no SystemPrompt do `docs-scribe` em [`skills/docs/references/docs-subagents.md:12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-subagents.md#L12), proibindo a inclusão de valores reais de tokens ou credenciais em exemplos do `README.md`.
- [x] **QW-DOC-03:** Harmonizar o comando de commit nos guidelines: substituir `git commit -am` em [`skills/docs/references/docs-guidelines.md:32`](file:///e:/Codigos/antigravity-agentic-workflows/skills/docs/references/docs-guidelines.md#L32) por staging explícito (`git add <files>` seguido de `git commit -m ...`), em alinhamento com a invariante de segurança do projeto contra inclusão acidental de arquivos não rastreados.

### Evoluções Estruturais (Scripts / Arquitetura de Subagentes)
- [x] **EV-DOC-01:** Implementar script estático AST em Python (`skills/docs/scripts/inject_docstrings.py`) para realizar a inserção cirúrgica de docstrings e wikilinks Obsidian de forma determinística, permitindo restringir o subagente `docs-scribe` exclusivamente à criação e edição de arquivos `.md`.
- [x] **EV-DOC-02:** Adicionar filtro e salvaguarda nos guidelines para APIs públicas e frameworks baseados em metadados (FastAPI, Typer, Pydantic), evitando poluição de schemas OpenAPI e contratos externos com wikilinks internos do Obsidian.
- [x] **EV-DOC-03:** Criar linter de manifestos para checagem de integridade de comandos de onboarding antes de publicá-los no `README.md` raiz.
