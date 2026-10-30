# Relatório de Auditoria OWASP LLM & Agentic (2025/2026) — Skill `/debug`

**Data da Auditoria:** 2026-10-30  
**Skill Auditada:** [`skills/debug/SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/SKILL.md)  
**Documentação Arquitetural:** [`doc/skills/debug/README.md`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/debug/README.md)  
**Modelo de Execução da Skill:** Main Orchestrator + Subagente `forensic-prober` (`Model: "inherit"`)  
**Status Geral de Segurança Agentic:** 🟡 Atenção Moderada (Arquitetura robusta com isolamento via subagente e RCA Gate, mas com riscos críticos de execução arbitrária de código em scripts de probing e destruição de dados em rollbacks globais)

---

## 1. Sumário Executivo e Perfil de Risco da Skill

A skill **`/debug`** é o componente de investigação forense e análise de causa raiz (RCA) do ecossistema Antigravity SDD 2.0. Seu propósito é diagnosticar e remediar falhas críticas em tempo de execução, condições de corrida, esgotamento de recursos e exceções complexas que resistiram à depuração reativa (`/test-fix`), aplicando a metodologia científica e o framework dos 5 Porquês (com foco obrigatório no mecanismo de escape na suíte de testes existente — Why #5).

### Arquitetura de Execução e Ferramentas Acionadas
A skill opera em um modelo híbrido bipartido:
1. **Orquestrador Principal (Maestro):** Realiza a triagem inicial (Step 1), lê o histórico de pivots do Obsidian (`02-auditorias/pivots-[slug].md`), submete o artefato formal [`root_cause_analysis.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/resources/rca-template.md) com pausa interativa obrigatória (`RequestFeedback: true` no Step 3) e aplica o fix cirúrgico aprovado com salvaguarda de regressão e Drift Gate determinístico (Step 4 via `check_sdd_drift.py`).
2. **Subagente `forensic-prober` (`Model: "inherit"`, Step 2):** Opera em sessão com permissão de escrita (`EnableWriteTools: true`) e execução de comandos CLI (`run_command`), encarregado de formular hipóteses concorrentes ($H_1, H_2$), criar scripts temporários de reprodução mínima (MRE) ou testes de sondagem, purgar os arquivos de *scratch* e entregar um relatório forense estruturado de volta ao chat principal.

### Superfície de Ataque e Riscos Identificados
- **Perspectiva A (Meta-Agentic Security):** A permissão de escrita e execução de scripts efêmeros (`scripts/reproduce_*.py`) no subagente `forensic-prober` sem sandbox de sistema operacional introduz um vetor de Execução Inesperada de Código (RCE - ASI05). Além disso, a ingestão direta de *stack traces*, mensagens de erro e *dumps* de rede expõe o fluxo a Injeção Indireta de Prompt (LLM01 / ASI01) e Vazamento de Credenciais/PII (LLM02) no relatório de RCA e no Obsidian Vault. O protocolo de recuperação pós-falha que sugere `git reset --hard HEAD` pode causar perda de trabalho em progresso.
- **Perspectiva B (Downstream Code Security):** O foco da skill é fazer o teste de regressão passar (Red $\rightarrow$ Green) e verificar integridade de contratos via AST (`check_sdd_drift.py`). Contudo, não há um gate de segurança estática (SAST/Bandit/Semgrep) antes do commit da correção, permitindo que a erradicação do bug introduza novas vulnerabilidades de código (como bypass de sanitização ou supressão de exceções).

---

## 2. Matriz de Conformidade: OWASP Top 10 for LLM Applications (2025/2026)

| Código | Categoria OWASP LLM (2025/2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **LLM01** | **Prompt Injection (Direta, Indireta ou Multimodal)** | **Crítica** | Delimitação de contexto no subagente isolado `forensic-prober` ([`debug-subagents.md#L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-subagents.md#L11)); isolamento de contexto zero. | *Stack traces*, mensagens de exceção e logs contendo payloads de ataque (ex.: em cabeçalhos HTTP ou dados de banco) são ingeridos crus no Step 1 ([`SKILL.md#L21`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/SKILL.md#L21)) e colados no template sem sanitização ([`rca-template.md#L24`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/resources/rca-template.md#L24)). | 🟡 Atenção |
| **LLM02** | **Sensitive Information Disclosure** | **Alta** | Não há chamadas diretas a ferramentas de busca externa (`search_web`) na skill padrão; a comunicação de dados fica restrita ao chat e ao Vault local. | Logs e *stack traces* de erros de produção frequentemente contêm segredos (tokens JWT, senhas em DSNs, PII de usuários). A skill orienta salvar evidências no RCA e arquivar no Obsidian (`02-auditorias/pivots-[slug].md`) sem sanitização de segredos prévia. | 🔴 Vulnerável |
| **LLM03** | **Excessive Agency** | **Alta** | RCA Gate obrigatório com pausa interativa (`RequestFeedback: true`, [`SKILL.md#L10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/SKILL.md#L10)); zero produção edits antes da aprovação humana. | O subagente `forensic-prober` possui `EnableWriteTools: true` irrestrito no runtime ([`debug-subagents.md#L10`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-subagents.md#L10)), baseando-se apenas em proibição por prompt (*soft boundary*) para não editar `src/`. | 🟡 Atenção |
| **LLM04** | **Supply Chain Vulnerabilities** | **Média** | Recomendações de pacotes ou upgrades de dependência na "Opção B" ([`rca-template.md#L74`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/resources/rca-template.md#L74)) são avaliadas pelo arquiteto humano antes da adoção. | Se a resolução do incidente envolver a instalação de novos pacotes para contornar um bug, a skill não aciona o script anti-slopsquatting (`verify_manifest_integrity.py` da skill `/infra`), arriscando pacotes alucinados. | 🟡 Atenção |
| **LLM05** | **Data and Model Poisoning** | **Média** | O histórico de pivôs do Obsidian (`02-auditorias/pivots-[slug].md`) é lido apenas como referência de decisões passadas ([`SKILL.md#L21`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/SKILL.md#L21)). | Notas do Obsidian corrompidas ou comprometidas podem induzir o agente a suposições arquiteturais falsas sobre comportamento esperado de pools ou concorrência. | 🟢 Conforme |
| **LLM06** | **Unbounded Consumption** | **Alta** | A investigação pesada de MRE/sondagem é delegada ao subagente, protegendo o chat principal contra *context bloat* de logs ([`doc/skills/debug/README.md#L12`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/debug/README.md#L12)). | Testes de sondagem de concorrência ou loops infinitos criados em `scripts/reproduce_*.py` podem travar a CLI sem *timeout* mandatado (`WaitMsBeforeAsync` ou `pytest --timeout`), provocando consumo excessivo de tempo/recursos. | 🟡 Atenção |
| **LLM07** | **System Prompt Leakage / Misinformation** | **Média** | A disciplina dos 5 Porquês e o teste de regressão em 2 fases (Red obrigatório antes de Green) previne consertos alucinados ([`SKILL.md#L13`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/SKILL.md#L13)). | A derivação do Why #5 (escape da suíte de teste) pode ser alucinada de forma convincente por complacência do modelo (*sycophancy*) para agradar o usuário, mascarando a real causa sistêmica. | 🟢 Conforme |
| **LLM08** | **Hidden Context Exposure** | **Baixa** | Isolamento de contexto no `forensic-prober` (`Context-Zero`), retornando apenas relatório sintético final ao Orquestrador ([`doc/skills/debug/README.md#L24`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/debug/README.md#L24)). | Arquivos de *scratch* deixados para trás caso o subagente falhe ou sofra *timeout* antes de purgar podem expor fragmentos de contexto forense em branches ativas. | 🟢 Conforme |
| **LLM09** | **Vector and Embedding Weaknesses** | **Informativa** | Não utiliza indexação vetorial ou RAG dinâmico opaco; utiliza leitura de notas e busca de arquivos estáticos no Obsidian. | N/A para esta skill diretamente (a governança lexical/semântica cabe à skill `/obsidian`). | 🟢 Conforme |
| **LLM10** | **Improper Output Handling** | **Alta** | Validação formal de contratos via AST determinístico (`check_sdd_drift.py`) impede que saídas de código quebrem assinaturas do SDD ([`SKILL.md#L28`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/SKILL.md#L28)). | Comandos de teste interpolam caminhos e nomes de teste diretamente no bash/powershell sem sanitização de aspas em argumentos (`python -m pytest [path]`). | 🟡 Atenção |

---

## 3. Matriz de Conformidade: OWASP Top 10 for Agentic Applications (2026)

| Código | Categoria OWASP Agentic (2026) | Relevância na Skill | Defesas Existentes (Evidências no Projeto) | Gaps / Vulnerabilidades Identificadas | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **ASI01** | **Agent Goal Hijack** | **Crítica** | Contrato estrito no prompt do `forensic-prober` focado exclusivamente em falsificar/confirmar $H_1, H_2$ ([`debug-subagents.md#L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-subagents.md#L11)). | Se o *traceback* ou arquivo reproduzido contiver instruções maliciosas injetadas (ex.: em respostas de mock HTTP simuladas), o subagente pode desviar sua investigação e escrever scripts hostis em `scripts/`. | 🔴 Vulnerável |
| **ASI02** | **Tool Misuse and Exploitation** | **Alta** | Invariante de expurgo de *scratch* (`Zero Dirt Working Tree`) verificado antes do handover ([`doc/skills/debug/README.md#L64-L71`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/debug/README.md#L64-L71)). | O uso de `git reset --hard HEAD` como mecanismo de recuperação pós-falha ([`debug-methodology.md#L34`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-methodology.md#L34), [`doc/skills/debug/README.md#L92`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/debug/README.md#L92)) pode destruir código e testes legítimos não commitados. | 🔴 Vulnerável |
| **ASI03** | **Identity and Privilege Abuse** | **Alta** | Modelo do subagente configurado como `inherit` para raciocínio complexo; separação nítida entre investigação e aplicação de fix ([`SKILL.md#L19-L24`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/SKILL.md#L19-L24)). | Subagente recebe permissão de escrita global na workspace sem confinamento a diretórios seguros (ex.: restrição em nível de tool para `scratch/` apenas). | 🟡 Atenção |
| **ASI04** | **Agentic Supply Chain Vulnerabilities** | **Média** | Subagente opera com instruções locais versionadas no repositório (`skills/debug/references/`); sem chamadas de subagentes externos desconhecidos. | Se o script de MRE importar pacotes inexistentes sugeridos por alucinação, pode haver exposição a ataques de *slopsquatting* no ambiente local do desenvolvedor. | 🟢 Conforme |
| **ASI05** | **Unexpected Code Execution (RCE)** | **Crítica** | Execução de testes de caracterização orientada à reprodução de defeitos em scripts temporários MRE ([`debug-methodology.md#L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-methodology.md#L11)). | O subagente escreve código Python arbitrário em `scripts/reproduce_*.py` e executa nativamente no shell do hospedeiro sem *sandbox*, *seccomp* ou análise estática prévia. | 🔴 Vulnerável |
| **ASI06** | **Memory and Context Poisoning** | **Alta** | Registro formal de lições aprendidas em `02-auditorias/pivots-[slug].md` e atualização do `dod-[slug].md` ([`debug-methodology.md#L35`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-methodology.md#L35)). | Diagnósticos errôneos ou 5 Porquês mal derivados são eternizados no Obsidian como verdade arquitetural permanente, envenenando planejamentos e implementações futuras. | 🟡 Atenção |
| **ASI07** | **Insecure Inter-Agent Communication** | **Alta** | Protocolo estruturado de handover: recebe hipóteses refutadas do `/test-fix` e entrega relatório sintético ao Orquestrador ([`SKILL.md#L21-L22`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/SKILL.md#L21-L22)). | A passagem de dados entre `/test-fix` e `/debug`, e entre `forensic-prober` e Orquestrador, não possui validação de schema (JSON Schema ou dataclass), utilizando Markdown livre vulnerável a parse ambíguo. | 🟡 Atenção |
| **ASI08** | **Cascading Failures** | **Alta** | Abertura de nova formulação de hipótese ($H_3$) caso a correção falhe, impedindo repetição estúpida de fixes ([`doc/skills/debug/README.md#L92`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/debug/README.md#L92)). | Se a hipótese $H_2$ for confirmada falsamente (ex.: por teste de sondagem com asserções fracas), o fix derivado pode degradar a estabilidade do sistema downstream sem que a suíte perceba. | 🟡 Atenção |
| **ASI09** | **Human-Agent Trust Exploitation** | **Alta** | RCA Gate transparente com comparação explícita de alternativas (Opção A vs Opção B com prós e contras) e pausa obrigatória ([`rca-template.md#L64-L79`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/resources/rca-template.md#L64-L79)). | Citação de padrões de autoridade formal (ex.: "Aligned with NIST SP 800-86 and ISO/IEC 27037" no [`rca-template.md#L3`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/resources/rca-template.md#L3)) pode gerar viés de automação no engenheiro, levando à aprovação precipitada da Opção A. | 🟡 Atenção |
| **ASI10** | **Rogue Agents** | **Média** | O subagente não possui permissão para aplicar a correção final; a edição em `src/` e o commit são monopólio do Orquestrador no Step 4 ([`doc/skills/debug/README.md#L59`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/debug/README.md#L59)). | Se o `forensic-prober` ignorar a regra de "zero production edits" devido a jailbreak ou perda de contexto, não há guardrail mecânico de pré-commit bloqueando edições fora de testes de sondagem. | 🟡 Atenção |

---

## 4. Pontos Críticos de Atenção (Achados Forenses Detalhados)

### 📌 [DEBUG-ASI05-01] Execução Inesperada de Código (RCE) via Scripts de Probing/MRE Arbitrários sem Sandbox
- **Categorias OWASP:** `ASI05 (Unexpected Code Execution)` / `ASI02 (Tool Misuse)` / `LLM10 (Improper Output Handling)`
- **Severidade:** 🔴 **Crítica**
- **Localização Exata:** [`debug-methodology.md#L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-methodology.md#L11), [`debug-subagents.md#L10-L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-subagents.md#L10-L11), [`doc/skills/debug/README.md#L66-L70`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/debug/README.md#L66-L70).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**  
  O subagente `forensic-prober` é instruído a: *"Write and run isolated probing tests or MRE scripts to confirm or falsify $H_1, H_2$"*, utilizando como exemplo arquivos como `scripts/reproduce_pool_leak.py`. O subagente gera o código fonte Python por meio de LLM e o executa imediatamente no terminal local da máquina de desenvolvimento via `pytest` ou `python scripts/reproduce_*.py`. Como essa execução ocorre no host (Windows) com os privilégios totais do desenvolvedor logado, qualquer alucinação de biblioteca, comando de sistema acidental (`os.system`, `shutil.rmtree`) ou payload malicioso originado de um *traceback* hostil executará de forma irrestrita, com capacidade de deletar arquivos do sistema, abrir portas de rede ou comprometer credenciais locais.
- **Recomendação Cirúrgica de Mitigação:**  
  1. Confinar os testes temporários exclusivamente ao diretório efêmero de scratch do agente (`<appDataDir>/brain/<conversation-id>/scratch/` ou `.tmp/probing/`).
  2. Implementar um filtro de integridade AST nos scripts gerados antes da invocação do interpretador, rejeitando construções com `eval`, `exec`, `subprocess`, `os.system`, chamadas de socket direto ou imports de rede não autorizados.
  3. Adicionar *timeout* estrito (ex.: `--timeout=15` no pytest ou limite em segundos no `run_command`) para mitigar deadlocks em simulações de concorrência.

---

### 📌 [DEBUG-LLM02-02] Vazamento e Persistência de Dados Sensíveis e PII em Relatórios RCA e Obsidian
- **Categorias OWASP:** `LLM02 (Sensitive Information Disclosure)` / `ASI06 (Memory and Context Poisoning)`
- **Severidade:** 🔴 **Alta**
- **Localização Exata:** [`rca-template.md#L21-L25`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/resources/rca-template.md#L21-L25), [`SKILL.md#L21`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/SKILL.md#L21), [`debug-methodology.md#L35`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-methodology.md#L35).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**  
  No Step 1, o Orquestrador ingere diretamente *stack traces* e logs de erros de produção que frequentemente contêm dados sensíveis, como Authorization Headers (`Bearer eyJ...`), variáveis de ambiente, *connection strings* de banco com senhas (`postgresql://user:pass@host/db`) ou dados pessoais de usuários envolvidos na requisição que causou a quebra. A diretiva em `rca-template.md` linha 24 solicita: *"Paste exact terminal error message or stack trace here"*. O documento de RCA gerado é posteriormente persistido em disco e resumos são integrados nas notas permanentes do Obsidian (`02-auditorias/pivots-[slug].md`), expondo credenciais e violando normas de privacidade (LGPD/GDPR) de forma duradoura no versionamento Git e no Vault de conhecimento.
- **Recomendação Cirúrgica de Mitigação:**  
  1. Inserir uma regra mandatória de higienização de segredos no Step 1 do [`SKILL.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/SKILL.md): executar varredura por regex em busca de padrões sensíveis (tokens, chaves, senhas, CPF/e-mails) substituindo-os por marcadores `[REDACTED_SECRET]` ou `[REDACTED_PII]` antes de injetar os dados no subagente ou no artefato RCA.
  2. Adicionar aviso explícito de sanitização no cabeçalho da seção 1.2 do [`rca-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/resources/rca-template.md).

---

### 📌 [DEBUG-ASI02-03] Risco de Destruição de Código Não Salvo por Rollback Cego via `git reset --hard HEAD`
- **Categorias OWASP:** `ASI02 (Tool Misuse and Exploitation)` / `LLM03 (Excessive Agency)` / `ASI08 (Cascading Failures)`
- **Severidade:** 🔴 **Alta**
- **Localização Exata:** [`debug-methodology.md#L34`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-methodology.md#L34), [`doc/skills/debug/README.md#L92`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/debug/README.md#L92).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**  
  O protocolo de salvaguarda de regressão define: *"Recovery: git reset --hard HEAD on failure"* e *"Caso a tentativa de correção cirúrgica continue falhando ou gere quebras colaterais em testes existentes, o Orquestrador executa imediatamente git reset --hard HEAD"*. Se o desenvolvedor chamou a skill `/debug` enquanto possuía modificações parciais ou arquivos não commitados em outras partes do projeto (fora do escopo do bug), ou se o novo teste permanente de regressão (`tests/regression/test_*_regression.py`) criado no Step 4 ainda não havia sido adicionado à *stage*, a execução incondicional de `git reset --hard HEAD` destruirá imediatamente todas essas alterações sem confirmação prévia e sem possibilidade de recuperação.
- **Recomendação Cirúrgica de Mitigação:**  
  1. Banir o uso de `git reset --hard HEAD` global como rotina automática de rollback na skill.
  2. Substituir por reversão direcionada exclusivamente aos arquivos de produção tocados pela tentativa de fix: `git checkout -- <modified_production_files>`, preservando intactos novos testes de regressão e arquivos do usuário não relacionados.
  3. Realizar `git stash create` antes de qualquer mutação de código de modo a criar um ponto de restauração seguro e determinístico.

---

### 📌 [DEBUG-LLM03-04] Escopo de Escrita do Subagente `forensic-prober` Confiado Apenas a Restrições de Prompt
- **Categorias OWASP:** `LLM03 (Excessive Agency)` / `ASI03 (Identity and Privilege Abuse)` / `ASI10 (Rogue Agents)`
- **Severidade:** 🟡 **Média**
- **Localização Exata:** [`debug-subagents.md#L10-L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-subagents.md#L10-L11), [`doc/skills/debug/README.md#L57`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/debug/README.md#L57).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**  
  O subagente `forensic-prober` é instanciado com o parâmetro `Write Tools: true` no nível de ambiente de ferramentas, o que na plataforma lhe confere permissão irrestrita para invocar `write_file` e `edit_file` em qualquer arquivo da árvore de diretórios. A restrição informada (*"restricted to temporary probing scripts; `src/` modification strictly forbidden"*) existe unicamente como texto dentro do `SystemPrompt`. Trata-se de uma salvaguarda suave (*soft boundary*). Sob contexto confuso, alucinação ou manipulação via injeção de prompt, o subagente pode sobrescrever arquivos de produção em `src/`, quebrar configurações em `config/` ou corromper arquivos da concepção em `01-concepcao/`.
- **Recomendação Cirúrgica de Mitigação:**  
  1. Adicionar uma validação de pós-condição obrigatória executada pelo Orquestrador logo após o retorno do `forensic-prober`: executar `git status --porcelain` e validar que nenhuma modificação em `src/`, `01-concepcao/` ou `00-core-rules/` ocorreu.
  2. Caso qualquer arquivo fora de caminhos efêmeros tenha sido tocado pelo subagente, rejeitar imediatamente a execução e reverter as alterações antes de avançar para o Step 3.

---

### 📌 [DEBUG-ASI07-05] Fragilidade no Protocolo de Handover entre `/test-fix` e `/debug` e Falta de Validação de Esquema
- **Categorias OWASP:** `ASI07 (Insecure Inter-Agent Communication)` / `ASI08 (Cascading Failures)`
- **Severidade:** 🟡 **Média**
- **Localização Exata:** [`SKILL.md#L21-L22`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/SKILL.md#L21-L22), [`doc/skills/debug/README.md#L54`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/debug/README.md#L54).
- **Descrição Técnica do Risco (Vetor de Ataque / Falha):**  
  No Step 1 de `/debug`, o Orquestrador ingere o *"Double-Strike context ($H_1, H_2$ falsified)"* gerado pelo `/test-fix`. Esse contexto é repassado em formato de texto livre em Markdown. Se o relatório de handover contiver interpretações erradas das tentativas falhas ou se a sintaxe do relatório for ambígua, o `forensic-prober` é instruído categoricamente a: *"Formulate competing hypotheses without repeating falsified `/test-fix` hypotheses"*. Se as hipóteses do `/test-fix` foram falsificadas devido a um erro superficial de digitação ou mock quebrado (e não porque a teoria da causa estivesse errada), o `/debug` descartará permanentemente o vetor correto, provocando um ciclo de falha em cascata (Cascading Failure).
- **Recomendação Cirúrgica de Mitigação:**  
  1. Padronizar o payload de handover em um formato estruturado (bloco YAML ou JSON) com campos explícitos para: `error_class`, `failing_frame`, `strike_1_mechanism`, `strike_2_mechanism`.
  2. Permitir expressamente no prompt do `forensic-prober` a reavaliação de hipóteses de `/test-fix` sob a condição de que novas evidências de testes de caracterização indiquem premissas falsas no diagnóstico reativo anterior.

---

## 5. Plano de Ação Priorizado para a Skill `/debug`

### ⚡ Quick Wins (Baixo Esforço / Alto Impacto)
- [x] **QW-01 (Sanitização de Segredos e Delimitação XML em Ingestão):** Inserir delimitadores `<forensic_evidence>` nos prompts e no [`rca-template.md`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/resources/rca-template.md#L23-L25), com instrução explícita para mascarar tokens de autenticação, senhas e chaves de API antes de colá-los no relatório.
- [x] **QW-02 (Rollback Cirúrgico Seguro sem `git reset --hard`):** Atualizar [`debug-methodology.md#L34`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-methodology.md#L34) e [`doc/skills/debug/README.md#L92`](file:///e:/Codigos/antigravity-agentic-workflows/doc/skills/debug/README.md#L92) para substituir o comando destrutivo global por `git checkout -- <modified_src_files>`, evitando a perda de código de trabalho do usuário.
- [x] **QW-03 (Timeouts Rígidos em Comandos de Reprodução):** Adicionar a flag `--timeout=15` (ou equivalente via pytest) nos comandos de teste e sondagem recomendados em [`debug-methodology.md#L11`](file:///e:/Codigos/antigravity-agentic-workflows/skills/debug/references/debug-methodology.md#L11) e no RCA Template para evitar congelamento por loops infinitos ou deadlocks simulados.

### 🏗️ Evoluções Estruturais (Scripts / Arquitetura de Subagentes)
- [x] **EV-01 (Diretório Confinado de Scratch & Purge Determinístico):** Padronizar a criação de MREs estritamente em `.tmp/forensic-scratch/` e implementar script utilitário de expurgo (`purge_scratch.py`) executado deterministicamente ao final da sessão do `forensic-prober`.
- [x] **EV-02 (Guardrail Mecânico de Integridade do Workspace):** Implementar verificação automática pelo Orquestrador via `git status --porcelain` ao receber o controle do `forensic-prober`. Se qualquer arquivo em `src/`, `01-concepcao/` ou `00-core-rules/` tiver sido alterado pelo subagente, abortar a execução com erro e reverter a contaminação.
- [ ] **EV-03 (Análise Estática de Segurança no Fix Cirúrgico):** Integrar ao Step 4 de `/debug`, logo após a suíte ficar verde e antes do commit, uma checagem de segurança estática local (ex.: varredura SAST básica no diff de produção) para certificar que a correção não introduziu novas vulnerabilidades de downstream code.
