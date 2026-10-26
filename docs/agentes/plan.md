# Agente de Concepção & Arquitetura (`/plan`) - Planejamento BDD, SDD e DoD (Fase 1)

O agente de **Concepção & Arquitetura** atua na **Fase 1 (Chat 1)** do ciclo de vida da feature no Antigravity IDE. Ele unifica em um único fluxo coeso o debate socrático de escopo, a validação de branches Git Flow, a especificação comportamental (BDD), a modelagem técnica de contratos (SDD) e a governança do Living DoD.

---

## ⛔ Restrição Universal da Fase 1

* **Zero Código de Produção:** É estritamente proibido escrever código de aplicação, componentes de interface ou testes automatizados durante a Fase 1. A finalidade exclusiva é o alinhamento arquitetural, modelagem de contratos e definição de critérios de aceite.

---

## 🚀 Pipeline de Execução em 5 Etapas

```mermaid
flowchart TD
    E1["Etapa 1: Debate Outcome-Based & Propostas (/grill-me)<br/><i>Referência: plan-debate.md</i>"] --> P1{"Aprovado?<br/>(Proceed no artefato)"}
    P1 --"Revisão/Ajuste"--> E1
    P1 --"Aprovado (Proceed)"--> E2["Etapa 2: Estratégia de Branch (Git Flow)<br/><i>Referência: plan-git.md</i>"]
    E2 --> E3["Etapa 3: Especificação BDD (Gherkin)<br/><i>Referência: plan-bdd.md</i>"]
    E3 --> E4["Etapa 4: Arquitetura SDD (UML + Contratos)<br/><i>Referência: plan-sdd.md</i>"]
    E4 --> E5["Etapa 5: Criação do Living DoD & Handover<br/><i>Referência: plan-dod.md & plan-git.md</i>"]
    E5 --> Next["<b>[NEXT STEP]</b><br/>Recomenda Chat 2 (/implement)"]
```

---

### Etapa 1: Debate Outcome-Based & Matriz de Propostas
1. **Foco no Estado Final Desejado:** Isola o resultado funcional e as regras de negócio reais, eliminando o "Problema XY". Sugestões do usuário são tratadas como hipóteses de trabalho.
2. **Entrevista Cirúrgica:** Realiza de 3 a 5 perguntas por turno (via ferramenta interativa `ask_question`) para esclarecer limites e casos excepcionais.
3. **Matriz Comparativa de Propostas:** Consolida o entendimento em até 3 alternativas no artefato `scope_proposals.md` (`RequestFeedback: true`):
   * **Proposta 1 (Pragmática / Incremental):** Menor atrito com código legado e menor custo.
   * **Proposta 2 (Arquiteturalmente Ideal / Escalável):** Alto desacoplamento, padrões modernos e prontidão para escala.
4. **Portão de Validação:** Avança somente após clique em **Proceed** ou aprovação formal da proposta escolhida.
* 💡 **Referência Operacional:** [`skills/plan/references/plan-debate.md`](../../skills/plan/references/plan-debate.md)

---

### Etapa 2: Estratégia de Ramificação (Git Flow)
1. Garante que o repositório não está trabalhando diretamente em `main` ou `develop`.
2. Valida via script automatizado:
   ```bash
   python skills/plan/scripts/validate_branch.py
   ```
3. Cria a branch da feature (ou worktree isolada):
   ```bash
   git checkout -b feature/[slug]
   ```
* 💡 **Referência Operacional:** [`skills/plan/references/plan-git.md`](../../skills/plan/references/plan-git.md)
* 🛠️ **Script de Validação:** [`skills/plan/scripts/validate_branch.py`](../../skills/plan/scripts/validate_branch.py)

---

### Etapa 3: Especificação Comportamental (BDD)
1. Traduz os requisitos em cenários formais em sintaxe pura Gherkin (`Given/When/Then`).
2. Garante cobertura de Caminho Feliz (*Happy Path*) e Caminhos de Exceção (*Unhappy Paths* / validações).
3. Persiste a especificação no Obsidian Vault em `01-concepcao/bdd-[slug].md`.
* 💡 **Referência Operacional:** [`skills/plan/references/plan-bdd.md`](../../skills/plan/references/plan-bdd.md)
* 📋 **Template de Documento:** [`skills/plan/resources/plan-template.md`](../../skills/plan/resources/plan-template.md)

---

### Etapa 4: Arquitetura Técnica & Contratos Tipados (SDD)
1. **Diagramação Segura em Mermaid.js:** Sequência e classes com rótulos de nós entre aspas duplas (`node["Exemplo"]`) para evitar quebras sintáticas.
2. **Contratos Tipados de Fronteira:** Interfaces, DTOs e mocks rigorosamente tipados na stack do projeto (Pydantic em Python, Zod em TypeScript, etc.).
3. **Matriz de Impacto de Arquivos:** Mapeia previamente arquivos adicionais e mutativos.
4. Valida a sintaxe e contratos via script:
   ```bash
   python skills/plan/scripts/validate_sdd_contracts.py 01-concepcao/sdd-[slug].md
   ```
5. Persiste o blueprint no Obsidian Vault em `01-concepcao/sdd-[slug].md`.
* 💡 **Referência Operacional:** [`skills/plan/references/plan-sdd.md`](../../skills/plan/references/plan-sdd.md)
* 📋 **Schema de Contrato:** [`skills/plan/resources/sdd-contract-template.yaml`](../../skills/plan/resources/sdd-contract-template.yaml)
* 🛠️ **Script de Validação:** [`skills/plan/scripts/validate_sdd_contracts.py`](../../skills/plan/scripts/validate_sdd_contracts.py)

---

### Etapa 5: Criação do Living DoD & Handover de Fase
1. Inicializa o documento vivo de aceite e rastreabilidade no Obsidian Vault em `01-concepcao/dod-[slug].md`.
2. Executa a consolidação semântica dos artefatos de concepção:
   ```bash
   git commit -m "docs(conception): BDD, SDD, and DoD specifications for [slug]"
   ```
3. Emite a diretriz de transição de fase:
   > **[NEXT STEP]** ➡️ *"🏗️ Fase 1 (Concepção & Arquitetura) concluída com sucesso! Abra um **NOVO CHAT (Chat 2)** e execute `/implement` para iniciar o ciclo de desenvolvimento TDD."*
* 💡 **Referências Operacionais:** [`skills/plan/references/plan-dod.md`](../../skills/plan/references/plan-dod.md) e [`skills/plan/references/plan-git.md`](../../skills/plan/references/plan-git.md)

---

## 🧰 Estrutura da Skill no Antigravity 2.0

* **Manifesto da Skill (`SKILL.md`):** [`skills/plan/SKILL.md`](../../skills/plan/SKILL.md)
* **Guias Operacionais (`references/`):**
  * [`plan-debate.md`](../../skills/plan/references/plan-debate.md) — Debate Outcome-Based e matriz de propostas
  * [`plan-git.md`](../../skills/plan/references/plan-git.md) — Governança de branch e isolamento de worktree
  * [`plan-bdd.md`](../../skills/plan/references/plan-bdd.md) — Especificação comportamental pura em Gherkin
  * [`plan-sdd.md`](../../skills/plan/references/plan-sdd.md) — Blueprint técnico, diagramas Mermaid e contratos
  * [`plan-dod.md`](../../skills/plan/references/plan-dod.md) — Inicialização e portões de aceite da DoD
* **Templates & Schemas (`resources/`):**
  * [`plan-template.md`](../../skills/plan/resources/plan-template.md)
  * [`sdd-contract-template.yaml`](../../skills/plan/resources/sdd-contract-template.yaml)
* **Scripts de Validação (`scripts/`):**
  * [`validate_branch.py`](../../skills/plan/scripts/validate_branch.py)
  * [`validate_sdd_contracts.py`](../../skills/plan/scripts/validate_sdd_contracts.py)
* **Exemplos Práticos (`examples/`):**
  * [`plan-example.md`](../../skills/plan/examples/plan-example.md)
