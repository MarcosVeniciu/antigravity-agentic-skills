# Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/implement`

**Data da Auditoria:** 2026-10-30  
**Skill Auditada:** [`skills/implement/SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/SKILL.md)  
**Documentação Arquitetural:** [`doc/skills/implement/README.md`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/implement/README.md)  
**Modelo de Execução da Skill:** Main Orchestrator + Subagentes (`batch-implementer` [`inherit`, `Write: true`] e `goldfish-drift-auditor` [`flash_lite`, `Write: false`])  
**Status Geral de Segurança Agentic:** 🟢 Robusto com Pontos de Atenção

---

## 1. Sumário Executivo e Perfil de Risco da Skill

A skill `/implement` governa a Fase 2 do ciclo SDD 2.0 (Desenvolvimento TDD Iterativo em Lotes). Sua arquitetura implementa o isolamento de contexto (Elephant & Goldfish) despachando cada lote (*Batch*) para uma instância limpa do subagente `batch-implementer`, evitando o *Context Bloat* e a saturação de tracebacks. O fechamento é protegido pelo validador determinístico AST [`check_sdd_drift.py`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/scripts/check_sdd_drift.py) e pelo auditor cego `goldfish-drift-auditor`.

### Perfil de Superfície de Ataque
1. **Perspectiva A (Segurança Meta-Agêntica do Fluxo):**
   - **RCE Local via Testes:** Execução direta de `pytest` pelo `batch-implementer` e pelo Orquestrador sem sandboxing de processo ou isolamento de rede.
   - **Permissões de Escrita (`Write: true`):** O subagente possui escopo irrestrito no workspace, protegido unicamente por diretivas de System Prompt.
   - **Evasão do Drift Gate via Pivots Frágeis:** `check_sdd_drift.py` utiliza regex lexical sobre `pivots-[slug].md`, permitindo que tokens comuns autorizem arquivos arbitrários.
   - **Destrutividade Git:** Uso de `git reset --hard HEAD` na regra de Double-Strike sem criação prévia de stash de segurança.
2. **Perspectiva B (Segurança do Código Downstream):**
   - Enforçamento explícito de cenários de segurança e concorrência na matriz de testes unitários ([`tdd-test.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-test.md)).
   - Princípio da Inversão de Dependência (DIP) e isolamento de I/O via `unittest.mock.create_autospec`.
   - Ausência de ferramenta SAST automatizada (ex.: Bandit, Semgrep) embutida na esteira de saída da implementação.

---

## 2. Matriz de Conformidade: OWASP Top 10 for LLM Applications (2025/2026)

| Código | Categoria OWASP LLM (2025/2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **LLM01** | **Prompt Injection (Direta, Indireta ou Multimodal)** | Alta | Subagente `batch-implementer` lê fontes estritas: `task_list.md` e `01-concepcao/{bdd,sdd}-[slug].md` ([`tdd-subagents.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-subagents.md#L16)). | Textos em BDDs ou docstrings de terceiros contendo instruções adversariais podem instruir o modelo a alterar comandos de teste ou chamar endpoints externos. | 🟡 Atenção |
| **LLM02** | **Sensitive Information Disclosure** | Média-Alta | Invariante na matriz de testes ([`tdd-test.md:17`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-test.md#L17)) prescrevendo teste de mascaramento: `"secret not in caplog, ***REDACTED***"`. | O traceback de `pytest` ou logs do console em caso de falha de teste podem capturar e expor variáveis de ambiente (`.env`) no histórico do chat do agente. | 🟡 Atenção |
| **LLM03** | **Excessive Agency** | Crítica | Escopo segregado por lotes em `task_list.md` ([`tdd-subagents.md:6-10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-subagents.md#L6-L10)). Gate de aprovação humana no Step 1 (`RequestFeedback: true`). | `batch-implementer` possui `EnableWriteTools: true` irrestrito no disco, podendo alterar manifestos ou configs fora de `src/` e `tests/`. Possui permissão de rodar `git reset --hard HEAD` ([`tdd-code.md:28`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-code.md#L28)). | 🔴 Vulnerável |
| **LLM04** | **Supply Chain Vulnerabilities** | Média | Utilização estrita de biblioteca padrão (`ast`, `re`, `argparse`, `dataclasses`, `yaml`) no script determinístico [`check_sdd_drift.py:15-22`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/scripts/check_sdd_drift.py#L15-L22). | Subagente de código pode importar pacotes Python inexistentes ou não instalados no `requirements.txt` / `pyproject.toml` (Slopsquatting). | 🟡 Atenção |
| **LLM05** | **Data and Model Poisoning** | Média | Contratos arquiteturais selados em `01-concepcao/sdd-[slug].md` com validação determinística via AST. | Arquivo `02-auditorias/pivots-[slug].md` não possui validação de assinatura ou esquema rígido; uma injeção em pivots pode corromper a base de regras da skill. | 🟡 Atenção |
| **LLM06** | **Unbounded Consumption** | Baixa-Média | Isolamento de contexto em subagente efêmero por lote; regra de Double-Strike interrompe após 2 falhas ([`tdd-code.md:28`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-code.md#L28)). | Falta de limite explícito de iterações (`max_turns`) ou timeout de subprocesso na chamada a `pytest` caso um teste entre em deadlock concorrente. | 🟢 Conforme |
| **LLM07** | **System Prompt Leakage / Misinformation** | Média | Context-Zero no `goldfish-drift-auditor` ([`tdd-subagents.md:17`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-subagents.md#L17)); validação determinística de assinaturas via AST elimina alucinações. | `flash_lite` possui menor capacidade de discernimento e pode atestar conformidade em asserções superficiais ou vazias. | 🟢 Conforme |
| **LLM08** | **Hidden Context Exposure** | Baixa | Tracebacks e histórico de tentativas de lotes anteriores são expurgados ao fechar o subagente `batch-implementer` ([`doc/skills/implement/README.md:20`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/implement/README.md#L20)). | Nenhum vazamento detectado; isolamento atua exatamente prevenindo contaminação cruzada. | 🟢 Conforme |
| **LLM09** | **Vector and Embedding Weaknesses** | Baixa | A skill não utiliza banco vetorial proprietário para RAG; opera sobre arquivos locais explícitos via caminhos relativos determinísticos. | Não aplicável diretamente ao fluxo da skill. | 🟢 Conforme |
| **LLM10** | **Improper Output Handling** | Média-Alta | `check_sdd_drift.py` utiliza `ast.parse` e `yaml.safe_load` ([`check_sdd_drift.py:97`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/scripts/check_sdd_drift.py#L97)), sem uso de `eval()` ou desserialização perigosa. | Saída do subagente (código-fonte gerado) é executada sem sanitização pelo interpretador Python no comando `pytest`. | 🟡 Atenção |

---

## 3. Matriz de Conformidade: OWASP Top 10 for Agentic Applications (2026)

| Código | Categoria OWASP Agentic (2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **ASI01** | **Agent Goal Hijack** | Alta | Objetivos rigidamente estruturados em `task_list.md` com critérios de aceite explícitos por lote ([`tdd-subagents.md:6-10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-subagents.md#L6-L10)). | Se um arquivo BDD ou docstring manipulada ordenar ignorar os critérios do lote e executar outra tarefa, o subagente não possui barreira semântica de contenção. | 🟡 Atenção |
| **ASI02** | **Tool Misuse and Exploitation** | Alta | Chamadas de CLI padronizadas no pipeline ([`SKILL.md:18,25,26`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/SKILL.md#L18-L26)); flags fixas (`--batch`, `--check-files`). | Subagente pode usar `run_command` para executar ferramentas do sistema fora do escopo de testes (ex.: utilitários de rede ou alterações globais no Git). | 🟡 Atenção |
| **ASI03** | **Identity and Privilege Abuse** | Alta | Segregação clara de modelos: `batch-implementer` (`inherit`, escrita) vs `goldfish-drift-auditor` (`flash_lite`, somente leitura) ([`tdd-subagents.md:14-17`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-subagents.md#L14-L17)). | Ausência de contenção de permissões de escrita por diretório no `batch-implementer`. Ele roda com o mesmo nível de privilégio do usuário no SO. | 🔴 Vulnerável |
| **ASI04** | **Agentic Supply Chain Vulnerabilities** | Média | Subagentes declarados estaticamente no repositório em referências versionadas (`references/tdd-subagents.md`). | Subagente pode instanciar pacotes alucinados via `import` dinâmico em código de produção ou testes. | 🟡 Atenção |
| **ASI05** | **Unexpected Code Execution (RCE)** | Crítica | Proibição de live I/O em testes unitários; mocks obrigatórios via `create_autospec` ([`tdd-test.md:4-5`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-test.md#L4-L5)). | RCE inerente ao ciclo TDD: o código gerado pelo LLM é executado pelo interpretador hospedeiro em `pytest` sem sandbox de processo ou virtualização de rede. | 🔴 Vulnerável |
| **ASI06** | **Memory and Context Poisoning** | Alta | `check_sdd_drift.py` valida AST contra `01-concepcao/sdd-[slug].md`; drift gera falha de exit code imediata ([`check_sdd_drift.py:414`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/scripts/check_sdd_drift.py#L414)). | O mecanismo `--pivots` aceita qualquer correspondência de palavra em `pivots-[slug].md` ([`check_sdd_drift.py:353-355`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/scripts/check_sdd_drift.py#L353-L355)), permitindo bypass inadvertido ou forjado do Drift Gate. | 🟡 Atenção |
| **ASI07** | **Insecure Inter-Agent Communication** | Média | Handover entre `batch-implementer` e Orquestrador intermediado por arquivos duráveis (`task_list.md`, disco) e git commits. | A saída de texto do `batch-implementer` contendo tabela de verificação não possui assinatura ou validação de integridade criptográfica. | 🟢 Conforme |
| **ASI08** | **Cascading Failures** | Alta | Exit Gate com 4 barreiras sequenciais no Step 3 (Suite, Drift, Audit, Closure) ([`SKILL.md:21-29`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/SKILL.md#L21-L29)). | Se o SDD contiver vulnerabilidades conceituais (ex.: armazenamento de senha em claro), a implementação TDD propagará o defeito com 100% de conformidade. | 🟡 Atenção |
| **ASI09** | **Human-Agent Trust Exploitation** | Alta | Auditor cego independente `goldfish-drift-auditor` emite veredito explícito `[PASS]: 100%_ACCEPTANCE_VERIFIED` ([`tdd-subagents.md:17`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-subagents.md#L17)). | O selo `[PASS]` atesta paridade de tags e assertividade aparente, mas não avalia ausência de vulnerabilidades de segurança (CWEs) no código implementado. | 🟡 Atenção |
| **ASI10** | **Rogue Agents** | Média-Alta | Limite estrito de escopo no lote ativo; regras invioláveis de Git proíbem commits em branches protegidas ou push ([`tdd-git.md:27-29`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-git.md#L27-L29)). | Subagente pode alterar código em outros módulos fora do lote ou modificar asserções se entrar em alucinação prolongada. | 🟡 Atenção |

---

## 4. Pontos Críticos de Atenção (Achados Forenses Detalhados)

### [IMP-ASI05-01] Execução Implícita de Código Não Confiável (RCE Local) via `pytest` sem Sandbox de Processo
- **Categorias OWASP:** ASI05 (Unexpected Code Execution), LLM03 (Excessive Agency)
- **Severidade:** `Alta`
- **Localização Exata:** [`skills/implement/references/tdd-subagents.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-subagents.md#L16), [`skills/implement/SKILL.md:15-18`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/SKILL.md#L15-L18)
- **Descrição Técnica do Risco:**
  O subagente `batch-implementer` gera testes unitários em `tests/unit/` e código em `src/`, executando `pytest` via terminal local para confirmar as fases RED, GREEN e BLUE. Como o interpretador Python carrega e executa imediatamente qualquer código presente nos módulos de teste (incluindo fixtures globais em `conftest.py` e código no corpo do arquivo), se o agente sofrer injeção de prompt indireta (ex.: vinda de uma docstring ou issue lida) ou alucinar chamadas perigosas (`__import__('os').system(...)`, decorators de bibliotecas maliciosas), a execução do `pytest` rodará código arbitrário com os privilégios totais da máquina do desenvolvedor.
- **Recomendação Cirúrgica de Mitigação:**
  Incluir no comando de teste a desativação de rede e restrições de plugins desnecessários via flags nativas do pytest (`python -m pytest -o addopts="" -p no:cacheprovider --override-ini="addopts=-s"`) e desativar explicitamente chamadas a subprocessos ou rede em ambiente de teste unitário via monkeypatch no `conftest.py` base.

---

### [IMP-ASI06-01] Fragilidade e Sobregeneralização no Bypass do Drift Gate via `--pivots` em `check_sdd_drift.py`
- **Categorias OWASP:** ASI06 (Memory and Context Poisoning), ASI02 (Tool Misuse), LLM05 (Model Poisoning)
- **Severidade:** `Média-Alta`
- **Localização Exata:** [`skills/implement/scripts/check_sdd_drift.py:295-296`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/scripts/check_sdd_drift.py#L295-L296), [`skills/implement/scripts/check_sdd_drift.py:353-356`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/scripts/check_sdd_drift.py#L353-L356)
- **Descrição Técnica do Risco:**
  A validação de autorização de desvios técnicos em `check_sdd_drift.py` é feita pela função:
  ```python
  def is_in_pivots(token: str) -> bool:
      return bool(pivots_text and re.search(rf"\b{re.escape(token)}\b", pivots_text))
  ```
  E na validação de arquivos não planejados (`--check-files`), o script executa:
  ```python
  pivoted = is_in_pivots(fpath.name) or any(
      is_in_pivots(part) for part in norm_path.split("/")
  )
  ```
  Se o documento `02-auditorias/pivots-[slug].md` contiver termos comuns como `"src"`, `"services"`, `"models"`, `"app"` ou `"utils"`, **qualquer arquivo não planejado criado dentro dessas pastas será automaticamente classificado como autorizado (`authorized_by_pivot=True`)**, passando com `exit 0`. Além disso, a nota de pivot não requer aprovação de assinatura humana, permitindo que o próprio agente registre um texto qualquer no arquivo de pivots para burlar a trava de drift.
- **Recomendação Cirúrgica de Mitigação:**
  Refatorar `check_sdd_drift.py` para exigir uma seção estruturada em formato YAML dentro do documento de pivot (ex.: ````yaml pivots: [{symbol: "ClassName.method", file: "src/domain/file.py", authorized_by: "human"}] ````). Eliminar a busca de `any(is_in_pivots(part) for part in norm_path.split("/"))`, exigindo correspondência exata do caminho relativo do arquivo.

---

### [IMP-ASI03-01] Falta de Confinamento de Escrita por Diretório no Subagente `batch-implementer`
- **Categorias OWASP:** ASI03 (Identity and Privilege Abuse), LLM03 (Excessive Agency), ASI10 (Rogue Agents)
- **Severidade:** `Média`
- **Localização Exata:** [`skills/implement/references/tdd-subagents.md:16`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-subagents.md#L16), [`doc/skills/implement/README.md:59`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/implement/README.md#L59)
- **Descrição Técnica do Risco:**
  O subagente `batch-implementer` é instanciado com permissão total de escrita (`EnableWriteTools: true`). Embora as diretivas textuais do System Prompt instruam que ele deve atuar apenas em `src/` e `tests/unit/` referentes ao Lote N, as ferramentas de escrita de arquivo não possuem restrição técnica em tempo de execução. Em caso de alucinação severa ou desvio de objetivo (Goal Hijack), o subagente pode sobrescrever arquivos de configuração de ambiente (`.env`), pipelines de CI/CD (`.github/workflows/`), scripts raiz ou o próprio código da skill.
- **Recomendação Cirúrgica de Mitigação:**
  Definir expressamente no contrato do subagente parâmetros de restrição de escopo de caminho ou incluir no script de governança Step 2.5 uma verificação estrita de git status antes do checkpoint (`git diff --name-only`), abortando e alertando o desenvolvedor caso qualquer arquivo fora de `src/` e `tests/` do lote tenha sido modificado.

---

### [IMP-ASI09-01] Falso Sentimento de Segurança por Avaliação Sintática do `goldfish-drift-auditor` (`flash_lite`)
- **Categorias OWASP:** ASI09 (Human-Agent Trust Exploitation), LLM07 (Misinformation)
- **Severidade:** `Média`
- **Localização Exata:** [`skills/implement/references/tdd-subagents.md:17`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-subagents.md#L17), [`skills/implement/SKILL.md:27`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/SKILL.md#L27)
- **Descrição Técnica do Risco:**
  O `goldfish-drift-auditor` utiliza o modelo `flash_lite` para auditar se todas as tags BDD (`@happy-path`, `@unhappy-path`, `@security`, `@concurrency`) possuem testes unitários associados com asserções reais. No entanto, por ser um modelo ultraleve com menor profundidade de raciocínio lógico, testes que contenham asserções semânticas fracas (como `assert response is not None` ou asserções que validam apenas tipagem mas ignoram restrições de regras de negócio ou de segurança) recebem aprovação com `[PASS]: 100%_ACCEPTANCE_VERIFIED`. O time humano confia no veredito como garantia de que todos os requisitos de segurança do BDD foram cumpridos.
- **Recomendação Cirúrgica de Mitigação:**
  Instruir no prompt do `goldfish-drift-auditor` a exigência de checagem contra asserções triviais ou genéricas (ex.: banir explicitamente `assert result is not None`, `assert len(x) >= 0`) em cenários com a tag `@security`, exigindo asserções de conteúdo e mascaramento específicas.

---

### [IMP-LLM03-01] Execução Destrutiva de `git reset --hard HEAD` sem Backup de Modificações do Desenvolvedor
- **Categorias OWASP:** LLM03 (Excessive Agency), ASI02 (Tool Misuse)
- **Severidade:** `Baixa-Média`
- **Localização Exata:** [`skills/implement/references/tdd-code.md:28`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-code.md#L28), [`skills/implement/references/tdd-git.md:9`](file:///e:/Codigos/antigravity-agentic-workflows/skills/implement/references/tdd-git.md#L9)
- **Descrição Técnica do Risco:**
  A política de Double-Strike estabelece que, se o subagente falhar mais de 2 vezes consecutivas em fazer o teste passar, deve rodar `git reset --hard HEAD` para restaurar o baseline verde. Caso o usuário ou o agente tenha alterações não comitadas em outros arquivos do projeto durante o ciclo, o comando descarta irreversivelmente todo o trabalho não salvo no índice do Git sem confirmação prévia nem criação de um commit temporário de segurança ou stash.
- **Recomendação Cirúrgica de Mitigação:**
  Substituir o comando destrutivo direto por um protocolo de salvaguarda: `git stash create` ou `git checkout -b rescue-strike-[timestamp]` antes de invocar o `git reset --hard HEAD`, garantindo que nenhuma alteração de trabalho seja permanentemente perdida no ambiente de desenvolvimento.

---

## 5. Plano de Ação Priorizado para a Skill `/implement`

### Quick Wins (Baixo Esforço / Alto Impacto)
- [ ] **Endurecimento de `check_sdd_drift.py`:** Remover a validação de partes de diretório (`any(is_in_pivots(part) for part in norm_path.split("/"))`) nas linhas 353-355, exigindo caminho relativo exato ou nome de classe qualificado para concessão de pivot.
- [ ] **Salvaguarda de Git Rollback em `tdd-git.md`:** Alterar a instrução de Double-Strike para executar `git stash push -m "rescue-strike-checkpoint"` antes de rodar `git reset --hard HEAD`.
- [ ] **Adição de Validação de Asserções Específicas em `goldfish-drift-auditor`:** Adicionar no System Prompt do auditor a proibição expressa de asserções triviais (`assert x is not None`, `assert True`) para cenários marcados com `@security`.

### Evoluções Estruturais (Scripts / Arquitetura de Subagentes)
- [ ] **Schema YAML Rígido para Notas de Pivô:** Modificar `check_sdd_drift.py` para processar apenas blocos ```yaml estruturados dentro de `02-auditorias/pivots-[slug].md`, exigindo o campo `authorized_by: "human"`.
- [ ] **Verificação de Integridade de Escopo Pós-Lote no Step 2.5:** Inserir um hook de validação no Orquestrador que confere se o git diff do lote tocou exclusivamente arquivos de `src/` e `tests/unit/` pertencentes ao Lote N planejado antes de gravar o checkpoint.
- [ ] **Isolamento de Execução de Testes (Sandbox Fixtures):** Configurar um plugin ou fixture padrão no repositório de testes que bloqueia chamadas externas de rede (`socket.connect`) e subprocessos durante a execução de `pytest tests/unit/`.
