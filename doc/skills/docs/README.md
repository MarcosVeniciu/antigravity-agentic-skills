# Arquitetura da Skill `/docs` (SDD 2.0 — Cost-Efficient Flash Scribe & Feature Freeze)

> [!IMPORTANT]
> **Documento Exclusivo de Engenharia e Manutenção da Skill `/docs`:**
> Este documento reside em `doc/docs/README.md` e detalha a especificação arquitetural da evolução da skill `/docs` para o modelo SDD 2.0. Ele **não** é instalado em `~/.gemini/config/skills/` nem em `.agents/skills/`, garantindo **zero poluição de contexto** para o agente em produção.

---

## 1. O Problema Resolvido: Desperdício de Janela Nobre, Regressões Sintáticas e Comandos Fictícios

Na fase de documentação técnica tradicional executada no chat principal por um único agente:
1. **Desperdício de Tokens de Raciocínio de Alta Capacidade:** Na Fase 5, a arquitetura e a implementação da feature já estão consolidadas e auditadas. Usar o modelo de raciocínio principal (`Model: "inherit"`) para ler integralmente dezenas de arquivos de código e gerar documentação estruturada consome cotas elevadas e incha o contexto com operações mecânicas de escrita.
2. **Risco de Alteração Acidental de Lógica de Produção:** Ao inserir docstrings ou anotações diretamente nos arquivos-fonte, agentes frequentemente alteram acidentalmente identações, linhas de controle de fluxo ou expressões, introduzindo regressões sintáticas não percebidas.
3. **Alucinação de Comandos Operacionais:** Guias de onboarding e READMEs costumam registrar comandos hipotéticos de execução, teste ou instalação que divergem dos manifestos reais configurados no repositório (`pyproject.toml`, `package.json`, etc.).
4. **Falta de Rastreabilidade Bidirecional com a Concepção:** Módulos e classes recém-criados perdem a conexão com suas especificações originais por não conterem referências formais às notas do Obsidian Vault (`[[sdd-[slug]]]`).
5. **Quebra Precoce da Disciplina de Git Flow:** Tentativas de realizar merge da feature branch diretamente em `develop` ou `main` ainda durante a fase de documentação, ignorando o processo formal e matematicamente auditado do `/release`.

---

## 2. Nova Arquitetura: Orquestrador + Subagente `docs-scribe` (`Model: "flash"`) + Verificação Estática Zero-RCE (`py_compile` & AST) + Feature Freeze

A skill `/docs` estabelece uma esteira enxuta, segura e econômica:
- **Agente Principal (Orquestrador):** Resolve a branch ativa e os arquivos alterados no diff (`git diff develop...HEAD --name-only`), extrai e valida os comandos reais dos manifestos contra a allowlist de gerenciadores padrão (`pip install`, `poetry install`, `pytest`, `npm ci`, `cargo build` — bloqueando pipes `curl`/`wget` suspeitos `[DOC-LLM04-04]`) no Step 1, delega a geração de artefatos ao subagente, executa a verificação estática Zero-RCE (`python -m py_compile <modified_python_files>`, `python skills/docs/scripts/verify_docstring_only.py <modified_python_files>` e `git diff <modified_py_files>` `[DOC-ASI05-02]`), atualiza o Living DoD no Obsidian (`01-concepcao/dod-[slug].md` no Step 3) e executa o commit semântico com staging explícito (`git add README.md <doc_files> && git commit -m ...` `[QW-DOC-03]`) selando o *Feature Freeze* da branch (Step 4).
- **Subagente `docs-scribe` (`Model: "flash"`, Step 2):** Opera em sessão isolada sem permissão de execução de comandos (`run_command` proibido `[DOC-ASI03-01]`), tratando comentários e código-fonte como `<untrusted_source_code>` e jamais expondo segredos reais do `.env` (`[QW-DOC-02]`): cria e atualiza `README.md` de módulo com diagramas Mermaid seguros (rótulos entre aspas duplas) e enriquece docstrings no código interno com anotações de rastreabilidade `[[sdd-[slug]]]` (preservando schemas OpenAPI/FastAPI/Typer/Pydantic sem wikilinks internos `[DOC-ASI09-03]`).

```mermaid
flowchart TD
    subgraph MainChat["Agente Principal (Orquestrador / Maestro)"]
        S1["<b>Step 1: Resolução de Contexto & Manifestos</b><br/>• git branch + git diff develop...HEAD --name-only<br/>• Extrai comandos allowlisted (pip/poetry/npm/cargo)<br/>• Localiza bdd-[slug].md, sdd-[slug].md e dod-[slug].md"]
        V["<b>Step 2.3: Syntax & AST Guard (Zero-RCE)</b><br/>• python -m py_compile &lt;modified_py_files&gt;<br/>• verify_docstring_only.py &amp; git diff<br/>• Garante zero mutação lógica de AST"]
        S3["<b>Step 3: Finalização do Living DoD</b><br/>• Marca [x] no item de documentação técnica<br/>• Registra fechamento na timeline do dod-[slug].md"]
        S4["<b>Step 4: Commit Semântico & Feature Freeze</b><br/>• Staging explícito: git add README.md &lt;doc_files&gt;<br/>• Commit: docs(feature): ...<br/>• Preserva Feature Freeze (Zero Merge no /docs)<br/>• Handover oficial para /release"]
    end

    subgraph SubDocs["Step 2: Subagente docs-scribe (Model: flash | Sem run_command)"]
        direction LR
        M["<b>1. READMEs de Módulo</b><br/>Gera doc-template.md<br/>Mermaid com aspas duplas<br/>e wikilinks [[sdd-[slug]]]"] --> D["<b>2. Docstrings Não-Destrutivas</b><br/>Injeta docstrings padronizadas<br/>(Exceção OpenAPI/CLI respeitada)<br/>Zero alteração de lógica"]
    end

    S1 -->|"Despacha Escopo (<untrusted_source_code>)"| M
    D -->|"Resumo de Arquivos Editados"| V
    V --> S3
    S3 --> S4
```

---

## 3. Matriz de Responsabilidades dos Agentes

| Etapa | Responsável | Modelo (`invoke_subagent`) | Permissão de Ferramentas | Insumos Recebidos | Entregável |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Step 1: Resolução de Escopo & Manifestos** | **Orquestrador Principal** | Sessão Ativa | Somente Leitura / CLI | `git diff develop...HEAD`, manifestos do repo (`pyproject.toml`, etc.), `01-concepcao/`. | Lista de arquivos do diff, comandos operacionais allowlisted e caminhos das especificações. |
| **Step 2: Geração de Docs & Enriquecimento de Código** | **Subagente `docs-scribe`** | `Model: "flash"` | Escrita de Docs/Docstrings (`run_command` **PROIBIDO**) | Lista de arquivos modificados (`<untrusted_source_code>`), comandos allowlisted, `01-concepcao/sdd-[slug].md` e [`doc-template.md`](../../skills/docs/resources/doc-template.md). | READMEs de módulo estruturados (sem segredos de `.env`), docstrings com `[[sdd-[slug]]]` (exceto rotas OpenAPI/CLI públicas) e resumo conciso. |
| **Step 2.3: Syntax & AST Guard (Zero-RCE)** | **Orquestrador Principal** | Sessão Ativa | CLI Estático | Arquivos `.py` modificados pelo `docs-scribe`. | Validação estática `python -m py_compile <modified_python_files>`, `verify_docstring_only.py` e `git diff` 100% aprovados. |
| **Step 3: Finalização do Living DoD** | **Orquestrador Principal** | Sessão Ativa | Escrita via `@obsidian` | Resumo de conclusão + `01-concepcao/dod-[slug].md`. | Checkbox de documentação marcado (`[x]`) e evento registrado na timeline cronológica do DoD. |
| **Step 4: Semantic Commit & Feature Freeze** | **Orquestrador Principal** | Sessão Ativa | Git Add Explícito & Commit | Árvore de trabalho atualizada com documentação e código verificado. | `git add README.md <doc_files> && git commit -m "docs(feature): ..."`, branch congelada (*Feature Freeze*) e aviso de transição para `/release`. |

---

## 4. Estratégia de Custo e Eficiência: Offloading para `Model: "flash"`

A delegação da geração de documentação para o subagente `docs-scribe` no perfil `Model: "flash"` oferece vantagens arquiteturais essenciais:
1. **Otimização Extrema de Cotas:** O modelo `flash` é altamente veloz e possui custo por token significativamente menor, executando tarefas estruturadas de preenchimento de templates e docstrings sem desperdiçar recursos dos modelos de raciocínio nobre.
2. **Isolamento de I/O em Massa:** A leitura detalhada de múltiplos módulos-fonte e a escrita em vários pontos do projeto não sobrecarregam o histórico do chat principal, que permanece conciso para o acompanhamento do usuário.
3. **Fidelidade aos Padrões Pré-Estabelecidos:** Orientado estritamente por [`doc-template.md`](../../skills/docs/resources/doc-template.md) e [`docs-guidelines.md`](../../skills/docs/references/docs-guidelines.md), o `docs-scribe` gera tabelas de mapeamento de componentes e diagramas Mermaid uniformes.

---

## 5. Protocolo de Injeção Não-Destrutiva de Docstrings e Salvaguarda Estática (`py_compile` & AST)

Para erradicar qualquer possibilidade de efeitos colaterais ou execução arbitrária de código (RCE) na base de código durante a documentação:
- **Invariante de Lógica Intocada (Zero Logic Alteration):** O subagente está expressamente proibido de alterar estruturas de controle (`if`, `for`, `try`), expressões aritméticas/lógicas, nomes de variáveis, imports ou assinaturas de métodos. Sua atuação restringe-se estritamente à inserção de docstrings e comentários explicativos.
- **Padrão de Rastreabilidade com Obsidian e Exceção de Schemas Públicos (`[DOC-ASI09-03]`):** Cada docstring interna adicionada deve conter o vínculo direto com o blueprint de concepção da funcionalidade:
  ```python
  """
  Resumo operacional conciso da classe ou método.

  Ref: Obsidian note [[sdd-[slug]]]
  """
  ```
  *Salvaguarda OpenAPI/CLI:* Em endpoints públicos FastAPI, modelos Pydantic ou comandos CLI Typer/Click, wikilinks internos (`[[sdd-...]]`) **não** devem ser injetados na docstring pública para evitar vazamento de metadados internos no schema OpenAPI/Swagger.
- **Syntax & AST Guard Determinístico Zero-RCE (`[DOC-ASI05-02]` & `[DOC-ASI03-01]`):** Em vez de executar `pytest -q` (que importa pacotes dinamicamente e pode disparar RCE via fixtures), o Orquestrador valida os arquivos `.py` modificados de forma 100% estática:
  ```bash
  python -m py_compile <modified_python_files>
  python skills/docs/scripts/verify_docstring_only.py <modified_python_files>
  git --no-pager diff <modified_python_files>
  ```
  Isso garante matematicamente que nenhuma indentação, erro sintático ou mutação lógica de AST foi introduzida nas fontes alteradas, com zero risco de execução de código.

---

## 6. Governança de Feature Freeze & Handover para `/release`

Ao término da documentação, a feature atinge o estado de **Congelamento (*Feature Freeze*)**:
1. **Compromisso Semântico com Staging Explícito (`[QW-DOC-03]`):** Todas as alterações são consolidadas pelo Orquestrador através de staging explícito (proibido `git commit -am`):
   ```bash
   git add README.md <doc_files> 01-concepcao/dod-[slug].md
   git commit -m "docs(feature): technical documentation and docstrings for [slug]"
   ```
2. **Proibição de Merge Prematuro:** O Orquestrador **nunca** executa `git checkout develop` ou `git merge` dentro da skill `/docs`. A branch `feature/[slug]` permanece isolada e estática.
3. **Handover para a Fase de Publicação:** O ciclo individual da feature é considerado concluído com 100% de Living DoD preenchido. O Orquestrador orienta o usuário a abrir um novo contexto e acionar `/release` para a condução do gatekeeper de publicação, cálculo de SemVer 2.0.0 e finalização do Git Flow.
