# Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/refactor`

**Data da Auditoria:** 2026-10-30  
**Skill Auditada:** [`skills/refactor/SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md)  
**Documentação Arquitetural:** [`doc/skills/refactor/README.md`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/refactor/README.md)  
**Modelo de Execução da Skill:** Main Orchestrator + Subagente `solid-refactorer` (`inherit`, `EnableWriteTools: true`)  
**Status Geral de Segurança Agentic:** 🟢 Robusto com Pontos de Atenção

---

## 1. Sumário Executivo e Perfil de Risco da Skill

A skill `/refactor` governa a Fase 3 do ciclo SDD 2.0 (Macro-Refatoração e Consolidação Arquitetural). Sua missão é varrer o diff cumulativo da feature branch (`git diff develop...HEAD`) aplicando Clean Code, SOLID e eliminando complexidade ciclomática ($V(G) \le 10$) e ineficiências assintóticas ($O(N^2)$), sem alterar contratos prévios ou introduzir regressões. Para evitar o esgotamento da janela de contexto (*Context Bloat*) por repetidas execuções de testes, a refatoração é delegada ao subagente contextual isolado `solid-refactorer`.

### Perfil de Superfície de Ataque
1. **Perspectiva A (Segurança Meta-Agêntica do Fluxo):**
   - **Adulteração de Testes (*Assertion Tampering*):** O subagente `solid-refactorer` tem permissão irrestrita de escrita em disco (`Write: true`). Se uma refatoração quebrar um teste, o modelo pode ceder à tendência de "consertar" o teste em `tests/unit/` em vez de ajustar o código em `src/`, desrespeitando a regra de invariância comportamental.
   - **RCE Local via `pytest`:** O interpretador Python local é acionado a cada alvo refatorado para confirmar ausência de regressões, executando código não sanitizado diretamente no SO.
   - **Evasão do Gate de Complexidade:** O script determinístico [`ast_complexity.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py) expõe a flag `--exit-zero`, que permite ignorar bloqueios mesmo com violações graves de complexidade.
   - **Comandos Destrutivos:** Instrução de execução de `git reset --hard HEAD` na falha de alvos pelo subagente.
2. **Perspectiva B (Segurança do Código Downstream):**
   - **Fortalecimento contra DoS/Algorithmic Attacks:** A redução matemática de $V(G)$ e a eliminação de loops $O(N^2)$ e buscas lineares aninhadas eliminam potenciais vetores de exaustão de CPU (Denial of Service).
   - **Isolamento de Camadas via DIP:** A injeção de dependência via `typing.Protocol` desacopla a lógica de negócio do acesso direto ao banco ou serviços externos, criando limites de segurança testáveis.
   - **Risco de Dependências Ocultas:** A refatoração de padrões (ex.: Strategy, Repositórios) pode induzir o modelo a importar pacotes externos não rastreados (Slopsquatting).

---

## 2. Matriz de Conformidade: OWASP Top 10 for LLM Applications (2025/2026)

| Código | Categoria OWASP LLM (2025/2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **LLM01** | **Prompt Injection (Direta, Indireta ou Multimodal)** | Média-Alta | Leitura restrita ao diff da branch (`develop...HEAD`), contratos SDD e catálogo local ([`refactor-subagents.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L7)). | Comentários ou docstrings maliciosas presentes no código a ser refatorado podem tentar instruir o modelo a inserir backdoors ou ignorar regras de complexidade. | 🟡 Atenção |
| **LLM02** | **Sensitive Information Disclosure** | Média | Escopo estritamente focado em código-fonte de produção e testes unitários. | Testes executados via `pytest -v` podem vazar dados confidenciais ou segredos mockados nos logs do console se ocorrerem falhas. | 🟢 Conforme |
| **LLM03** | **Excessive Agency** | Crítica | Gate humano prévio na aprovação do mapeamento em `task_list.md` (`RequestFeedback: true`) ([`SKILL.md:15`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L15)). | `solid-refactorer` possui `EnableWriteTools: true` irrestrito no workspace. Pode editar arquivos de teste (violando a invariante de teste imutável) ou arquivos fora do diff da branch. | 🔴 Vulnerável |
| **LLM04** | **Supply Chain Vulnerabilities** | Média-Alta | O scanner determinístico `ast_complexity.py` utiliza 100% biblioteca padrão Python ([`ast_complexity.py:8-12`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py#L8-L12)). | Subagente pode introduzir pacotes externos ou dependências alucinadas (Slopsquatting) durante a extração de padrões SOLID sem registrar em manifestos. | 🟡 Atenção |
| **LLM05** | **Data and Model Poisoning** | Média | Contratos fixos em `01-concepcao/sdd-[slug].md` e catálogo fechado de transformações ([`solid-catalog.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/solid-catalog.md)). | Se a base de notas Obsidian (`02-auditorias/pivots-[slug].md`) for envenenada com pivots fictícios, o Drift Gate aceita remoções indevidas de métodos. | 🟡 Atenção |
| **LLM06** | **Unbounded Consumption** | Baixa-Média | Delimitação estrita do escopo ao diff (`git diff develop...HEAD`) e limite de 2 tentativas (Double-Strike) ([`refactor-git.md:9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-git.md#L9)). | Ausência de timeout de tempo real no subprocesso `pytest` e ausência de teto explícito de tokens por invocação do `solid-refactorer`. | 🟢 Conforme |
| **LLM07** | **System Prompt Leakage / Misinformation** | Baixa | Aferição de qualidade 100% matemática via `ast_complexity.py` e validação determinística de assinaturas via `check_sdd_drift.py`. | Risco baixo de alucinação de conformidade, pois as métricas de saída são computadas via AST e não por avaliação aberta do modelo. | 🟢 Conforme |
| **LLM08** | **Hidden Context Exposure** | Baixa | `solid-refactorer` é context-isolated: descarta tracebacks e histórico de refatoração iterativa entre alvos ([`doc/skills/refactor/README.md:22`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/refactor/README.md#L22)). | Nenhum vazamento detectado entre contextos de subagentes. | 🟢 Conforme |
| **LLM09** | **Vector and Embedding Weaknesses** | Baixa | Não utiliza base vetorial ou embeddings proprietários no fluxo da skill. | Não aplicável. | 🟢 Conforme |
| **LLM10** | **Improper Output Handling** | Média-Alta | Análise sintática segura via módulo padrão `ast` sem uso de `eval()` ou `exec()` ([`ast_complexity.py:118`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py#L118)). | O código refatorado pelo subagente é salvo diretamente em disco e executado em seguida pelo interpretador Python no comando `pytest`. | 🟡 Atenção |

---

## 3. Matriz de Conformidade: OWASP Top 10 for Agentic Applications (2026)

| Código | Categoria OWASP Agentic (2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **ASI01** | **Agent Goal Hijack** | Alta | Backlog com metas cirúrgicas pré-mapeadas e aprovadas em `task_list.md` ([`SKILL.md:15`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L15)). | Código legado malicioso no repositório poderia conter instruções adversariais em docstrings ou comentários tentando desviar o foco da refatoração. | 🟡 Atenção |
| **ASI02** | **Tool Misuse and Exploitation** | Alta | Linha de comando determinística padronizada com thresholds definidos (`--threshold 10`) ([`SKILL.md:24-25`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L24-L25)). | Existência do argumento `--exit-zero` em `ast_complexity.py` ([`ast_complexity.py:142`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py#L142)) permite que o agente evada o bloqueio de funções complexas. | 🔴 Vulnerável |
| **ASI03** | **Identity and Privilege Abuse** | Alta | Papéis claros: Orquestrador governa e fecha a fase; `solid-refactorer` atua cirurgicamente nos alvos ([`doc/skills/refactor/README.md:51-57`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/refactor/README.md#L51-L57)). | O subagente `solid-refactorer` herda privilégios do modelo principal (`inherit`) e possui ferramenta de escrita ativa sem restrição de path. | 🔴 Vulnerável |
| **ASI04** | **Agentic Supply Chain Vulnerabilities** | Média | Protocolo de subagente estático registrado na documentação interna (`references/refactor-subagents.md`). | Pacotes alucinados importados no código de produção durante a refatoração podem contaminar a supply chain do projeto downstream. | 🟡 Atenção |
| **ASI05** | **Unexpected Code Execution (RCE)** | Crítica | Análise de complexidade via `ast_complexity.py` é 100% estática (AST seguro). | Execução direta de `pytest tests/unit/` pelo subagente e pelo Orquestrador sem sandboxing de processo ou container efêmero. | 🔴 Vulnerável |
| **ASI06** | **Memory and Context Poisoning** | Alta | Validação cruzada com SDD Drift Gate (`check_sdd_drift.py --batch`) impede remoção ou alteração de métodos declarados ([`refactor-subagents.md:14`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L14)). | O arquivo `01-concepcao/dod-[slug].md` e `02-auditorias/pivots-[slug].md` podem ser alterados para mascarar ausência de conformidade. | 🟡 Atenção |
| **ASI07** | **Insecure Inter-Agent Communication** | Baixa-Média | Comunicação estruturada baseada em schema de Matriz de Evidências ([`refactor-dod.md:16-19`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-dod.md#L16-L19)). | Falta de validação programática da tabela Markdown retornada pelo subagente (o Orquestrador confia no texto retornado). | 🟢 Conforme |
| **ASI08** | **Cascading Failures** | Alta | Verificação de entrada obrigatória (Entry Gate: 100% de testes verdes antes de qualquer edição) ([`refactor-dod.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-dod.md#L7)). | Se o código modificado tiver baixa cobertura de testes prévia, uma refatoração pode alterar regras de negócio silenciosamente e passar nos testes com sucesso. | 🟡 Atenção |
| **ASI09** | **Human-Agent Trust Exploitation** | Alta | Relatório formal de consolidação (`refactor-report-template.md`) e tabela com $V(G)$ antes e depois ([`refactor-report-template.md:22-27`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/resources/refactor-report-template.md#L22-L27)). | A métrica $V(G)$ em queda rápida pode dar ao desenvolvedor uma falsa impressão de perfeição técnica, ocultando novos race conditions ou vazamentos de memória. | 🟡 Atenção |
| **ASI10** | **Rogue Agents** | Média-Alta | Regras de versão rígidas: proibido push, proibido commit em branches principais, rollback via `git reset --hard` ([`refactor-git.md:27-31`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-git.md#L27-L31)). | A regra de ouro "Zero Tampering: Never modify tests" é baseada exclusivamente em prompt e não tem trava física de permissão de arquivo. | 🔴 Vulnerável |

---

## 4. Pontos Críticos de Atenção (Achados Forenses Detalhados)

### [REF-ASI02-01] Risco Crítico de Modificação Oportunista de Testes (*Assertion Tampering*) pelo `solid-refactorer`
- **Categorias OWASP:** ASI02 (Tool Misuse), ASI10 (Rogue Agents), LLM03 (Excessive Agency)
- **Severidade:** `Alta`
- **Localização Exata:** [`skills/refactor/references/refactor-subagents.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L7), [`skills/refactor/references/refactor-git.md:30`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-git.md#L30)
- **Descrição Técnica do Risco:**
  O subagente `solid-refactorer` é instanciado com `EnableWriteTools: true` e acesso global de escrita no projeto. O princípio fundamental da refatoração é a **invariância comportamental**, garantida pela estabilidade e imutabilidade dos testes unitários existentes. Embora a regra inviolável do Git declare expressamente *"Zero Tampering: Never modify tests or weaken assertions to force pass"* ([`refactor-git.md:30`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-git.md#L30)), essa salvaguarda é puramente declarativa no prompt.
  Quando um LLM executa uma refatoração profunda e quebra testes existentes (ex.: mudando ordem de parâmetros internos ou comportamento sutil), o modelo tem forte tendência estocástica a editar o arquivo `tests/unit/test_*.py` para "corrigir a asserção", mascarando a quebra de contrato comportamental para evitar o rollback de Double-Strike.
- **Recomendação Cirúrgica de Mitigação:**
  No Step 4 de verificação pelo Orquestrador, antes do squash commit, executar um comando de auditoria de integridade do Git:
  ```bash
  git diff --name-only <PHASE_START_HASH>...HEAD tests/
  ```
  Se qualquer arquivo de teste apresentar modificação em relação ao início da Fase 3, o Orquestrador deve abortar a fase imediatamente com falha de segurança, rejeitando a refatoração.

---

### [REF-ASI06-01] Possibilidade de Evasão do Gate de Complexidade via Parâmetro `--exit-zero` em `ast_complexity.py`
- **Categorias OWASP:** ASI06 (Context and Memory Poisoning), ASI02 (Tool Misuse), LLM03 (Excessive Agency)
- **Severidade:** `Média-Alta`
- **Localização Exata:** [`skills/refactor/scripts/ast_complexity.py:142`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py#L142), [`skills/refactor/scripts/ast_complexity.py:222-224`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py#L222-L224)
- **Descrição Técnica do Risco:**
  O analisador determinístico `ast_complexity.py` aceita uma flag de linha de comando:
  ```python
  parser.add_argument("--exit-zero", action="store_true", help="Always exit with 0 (non-blocking mode)")
  ...
  if args.exit_zero:
      sys.exit(0)
  ```
  Embora útil para relatórios exploratórios humanos, a presença dessa flag exposta permite que um subagente em loop de falhas ou com alucinação execute `python skills/refactor/scripts/ast_complexity.py <file> --threshold 10 --exit-zero` para reportar falsamente sucesso nos exit gates (Step 4.1), permitindo que métodos com $V(G) > 10$ ou erros graves de sintaxe passem desapercebidos para a esteira de review.
- **Recomendação Cirúrgica de Mitigação:**
  Remover a flag `--exit-zero` da versão de produção de `ast_complexity.py` ou torná-la mutuamente exclusiva com a esteira automatizada da skill, garantindo que qualquer função acima do threshold ou arquivo com erro de parsing resulte estritamente em código de saída `exit 1`.

---

### [REF-ASI05-01] Execução Recorrente de `pytest` sem Sandboxing no Interpretador Hospedeiro
- **Categorias OWASP:** ASI05 (Unexpected Code Execution), LLM03 (Excessive Agency)
- **Severidade:** `Média-Alta`
- **Localização Exata:** [`skills/refactor/references/refactor-subagents.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L7), [`skills/refactor/SKILL.md:14-16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L14-L16)
- **Descrição Técnica do Risco:**
  Durante o loop de refatoração, o subagente `solid-refactorer` reexecuta continuamente a suíte `pytest tests/unit/` para cada alvo alterado. A execução do pytest importa dinamicamente o código refatorado e os testes. Caso o código-fonte sob refatoração contenha payloads maliciosos herdados ou se o modelo injetar uma dependência de sistema vulnerável, o pytest roda com os privilégios totais do usuário local no Windows, sem restrição de chamada ao sistema operacional (`os.system`, `subprocess`) ou chamadas de socket de rede.
- **Recomendação Cirúrgica de Mitigação:**
  Instruir no pipeline de execução o bloqueio de rede no pytest (ex.: `--override-ini="addopts=-p no:network"`) ou execução através de container isolado de desenvolvimento quando disponível no ambiente.

---

### [REF-LLM04-01] Risco de Injeção de Dependências Não Versionadas ou Alucinadas (Slopsquatting) Durante Refatoração SOLID
- **Categorias OWASP:** LLM04 (Supply Chain Vulnerabilities), ASI04 (Agentic Supply Chain Vulnerabilities)
- **Severidade:** `Média`
- **Localização Exata:** [`skills/refactor/references/solid-catalog.md:16-19`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/solid-catalog.md#L16-L19), [`skills/refactor/references/refactor-subagents.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-subagents.md#L7)
- **Descrição Técnica do Risco:**
  Ao orientar a aplicação de padrões avançados (como Inversão de Dependência, Strategy Pattern e Segregação de Interfaces), o modelo pode alucinar ou introduzir pacotes externos de injeção de dependência (ex.: `dependency-injector`, `injector`) ou bibliotecas utilitárias de terceiros não registradas no `pyproject.toml` / `requirements.txt`. Além do risco de quebrar o build do CI/CD, isso expõe o projeto ao risco de *Slopsquatting* (pacotes com nomes gerados por IA que foram previamente registrados por invasores em repositórios públicos como o PyPI).
- **Recomendação Cirúrgica de Mitigação:**
  Adicionar uma diretiva explícita no catálogo SOLID e no System Prompt do `solid-refactorer`: *"Zero novas dependências: use exclusivamente recursos da biblioteca padrão Python (ex.: `typing.Protocol`, `dataclasses`, `functools`) ou pacotes já presentes no manifesto do projeto. Não adicione novos `import` de bibliotecas externas sem autorização formal."*

---

### [REF-ASI08-01] Risco de Falsos Negativos de Regressão em Código sem Cobertura Prévia no Diff
- **Categorias OWASP:** ASI08 (Cascading Failures), ASI09 (Human-Agent Trust Exploitation)
- **Severidade:** `Baixa-Média`
- **Localização Exata:** [`skills/refactor/SKILL.md:14`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md#L14), [`skills/refactor/references/refactor-dod.md:7`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/references/refactor-dod.md#L7)
- **Descrição Técnica do Risco:**
  O Entry Gate da skill `/refactor` exige que `pytest tests/unit/ -v` esteja 100% verde antes de iniciar as edições. No entanto, o gate não valida a **taxa de cobertura de testes (line/branch coverage)** dos alvos que serão refatorados. Se uma função complexa com $V(G) = 15$ possuir apenas um teste nominal básico (Happy Path) que não exercita ramificações críticas de erro, a refatoração pode alterar o comportamento dessas ramificações desprotegidas. Os testes continuarão 100% verdes pós-refatoração, conferindo falsa confiança de que zero regressões foram introduzidas.
- **Recomendação Cirúrgica de Mitigação:**
  Adicionar no Step 1 (Entry Gate) uma verificação de cobertura nos arquivos do diff (`pytest --cov=<target_files> --cov-report=term-missing`). Se a cobertura de um módulo a ser refatorado estiver abaixo de um patamar seguro (ex.: 80%), a refatoração deve ser precedida pela adição de testes de caracterização (Approval/Golden Master tests) antes de qualquer transformação de código.

---

## 5. Plano de Ação Priorizado para a Skill `/refactor`

### Quick Wins (Baixo Esforço / Alto Impacto)
- [x] **Hardening do Exit Gate no Orquestrador contra Modificação de Testes:** Inserir a verificação `git diff --quiet <PHASE_START_HASH>...HEAD tests/` no Step 4 de [`SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/SKILL.md). Se os testes tiverem sido alterados, a execução falha e aborta o squash.
- [x] **Remoção da Flag `--exit-zero` em `ast_complexity.py`:** Eliminar o argumento não seguro da CLI em [`ast_complexity.py:142`](file:///e:/Codigos/antigravity-agentic-workflows/skills/refactor/scripts/ast_complexity.py#L142) para impedir bypasses mecânicos do teto $V(G) \le 10$.
- [x] **Salvaguarda de Git Rollback em `refactor-git.md`:** Alterar a instrução de Double-Strike para criar um `git stash` ou backup antes do comando `git reset --hard HEAD`.
- [x] **Invariante de Biblioteca Padrão em `solid-catalog.md`:** Declarar explicitamente que refatorações devem usar exclusivamente a biblioteca padrão Python (`typing.Protocol`, etc.), sem inclusão de novas dependências externas.

### Evoluções Estruturais (Scripts / Arquitetura de Subagentes)
- [x] **Gating de Cobertura Prévia no Step 1:** Integrar a medição de cobertura de ramificações (`pytest --cov`) no Entry Gate, alertando o arquiteto caso funções com $V(G) > 10$ não possuam testes suficientes para garantir refatoração segura.
- [ ] **Validador Programático da Matriz de Evidências:** Criar um script verificador que lê a tabela do relatório de refatoração gerada pelo subagente e confere contra os números reais de `ast_complexity.py`, evitando que métricas $V(G)$ alucinadas sejam aceitas.
- [ ] **Isolamento de Execução de Testes Unitários:** Encapsular o comando de teste em modo estrito de isolamento (sem acesso a sockets de rede externos e sem permissão de gravação fora do diretório temporário do projeto).
