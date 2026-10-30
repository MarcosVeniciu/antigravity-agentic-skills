# Arquitetura da Skill `/review` (SDD 2.0 — 5-Domain Parallel Map-Reduce)

> [!IMPORTANT]
> **Documento Exclusivo de Engenharia e Manutenção da Skill `/review`:**
> Este documento reside em `doc/review/README.md` e detalha a especificação arquitetural da evolução da skill `/review` para o modelo SDD 2.0 Map-Reduce. Ele **não** é instalado em `~/.gemini/config/skills/` nem em `.agents/skills/`, garantindo **zero poluição de contexto** para o agente em produção.

---

## 1. O Problema Resolvido: Fadiga de Atenção Sequencial e Conflito de Escrita

Na revisão tradicional de 5 domínios executada em série por um único agente (`Architecture -> Security -> Quality -> Performance -> Resilience`):
1. **Degradação *Lost-in-the-Middle*:** Ao chegar nos domínios 4 (Performance) e 5 (Resilience), a janela de contexto do agente já está saturada com 3 manuais de referência anteriores, outputs de scanners e 3 relatórios completos gerados, reduzindo a profundidade analítica nos últimos domínios.
2. **Desperdício de Tokens de Referência e Latência 5x Maior:** Mesmo no modo padrão (*Mode A — Audit-Only*), onde os 5 relatórios são totalmente independentes, o usuário aguardava 5 ciclos sequenciais.
3. **Risco de *Race Condition* em Arquivos no Mode B (`--fix`):** Se 5 subagentes paralelos editassem o mesmo arquivo `.py` simultaneamente para corrigir achados de diferentes domínios, sobrescreveriam o código uns dos outros.

---

## 2. Nova Arquitetura: Map-Reduce com 5 Subagentes Paralelos (`Model: "flash"`) + Drift Gate

A skill `/review` adota o padrão **Map-Reduce Arquitetural**:
- **Pre-Flight (Orquestrador):** Valida a suíte de testes (`pytest -v`), extrai o `git diff develop...HEAD` e executa de uma só vez os **4 scanners determinísticos** (`check_sdd_drift.py`, `check_arch_boundaries.py`, `scan_sinks.py`, `ast_complexity.py`).
- **Fase MAP (5 Subagentes `Model: "flash"` 100% em Paralelo):** No mesmo turno, o Orquestrador dispara os 5 auditores especialistas. Cada auditor carrega **apenas o guia do seu domínio** (`references/review-[domain].md`), inspeciona o diff e escreve exclusivamente o seu relatório (`02-auditorias/audit-[domain]-[slug].md`), **sem tocar no código-fonte (`src/` ou `tests/`)**.
- **Fase REDUCE (Orquestrador):** Valida os 5 relatórios, atualiza o Living DoD e, caso esteja em **Mode B (`--fix`)**, aplica as correções cirúrgicas de forma centralizada e livre de conflitos de concorrência.

```mermaid
flowchart TD
    subgraph MainPre["Step 1: Orquestrador — Entry Gate & Pre-Flight Scanners"]
        S1["1. Roda pytest -v (100% Verde)<br/>2. Extrai git diff develop...HEAD<br/>3. Executa os 4 Scanners CLI:<br/>• check_sdd_drift.py (Drift Gate)<br/>• check_arch_boundaries.py<br/>• scan_sinks.py<br/>• ast_complexity.py"]
    end

    subgraph MapPhase["Step 2 (MAP): 5 Subagentes em Paralelo no Mesmo Turno (Model: flash)"]
        direction LR
        A1["🏛️ <b>auditor-architecture</b><br/>Lê apenas review-architecture.md<br/>Avalia DIP, Camadas & SDD Drift<br/>Gera audit-architecture-[slug].md"]
        A2["🛡️ <b>auditor-security</b><br/>Lê apenas review-security.md<br/>Taint Analysis (Call Hierarchy 1-2x)<br/>Gera audit-security-[slug].md"]
        A3["🧹 <b>auditor-quality</b><br/>Lê apenas review-quality.md<br/>Avalia AST V(G) <= 10 & Clean Code<br/>Gera audit-quality-[slug].md"]
        A4["⚡ <b>auditor-performance</b><br/>Lê apenas review-performance.md<br/>Avalia N+1, Big-O & Streaming<br/>Gera audit-performance-[slug].md"]
        A5["🛟 <b>auditor-resilience</b><br/>Lê apenas review-resilience.md<br/>Avalia Timeouts, Idempotência & Retry<br/>Gera audit-resilience-[slug].md"]
    end

    subgraph ReducePhase["Steps 3 & 4 (REDUCE): Orquestrador — Consolidação & Mode B Remediation"]
        R1{"Modo de Operação?"}
        ModeA["<b>Mode A (Audit-Only Default)</b><br/>Verifica os 5 relatórios em 02-auditorias/<br/>Marca os 5 checkboxes em dod-[slug].md"]
        ModeB["<b>Mode B (--fix Authorized)</b><br/>Consolida findings dos 5 relatórios sem conflito,<br/>aplica surgical fixes em src/, re-roda scanners + pytest<br/>e grava checkpoints + commit audit(review)"]
        Handover["<b>Step 4: Handover</b><br/>Recomenda abertura de NOVO CHAT para /docs"]
    end

    S1 --> A1 & A2 & A3 & A4 & A5
    A1 & A2 & A3 & A4 & A5 --> R1
    R1 -->|"Mode A"| ModeA
    R1 -->|"Mode B (--fix)"| ModeB
    ModeA --> Handover
    ModeB --> Handover
```

---

## 3. Matriz de Responsabilidades dos Agentes

| Etapa / Agente | Modelo (`invoke_subagent`) | Guia Carregado (Isolamento de Contexto) | Scanner Base Recebido | Arquivo Gerado / Ação |
| :--- | :---: | :--- | :--- | :--- |
| **Step 1: Orquestrador (Pre-Flight)** | Sessão Ativa | `SKILL.md` | Executa os 4 scripts CLI + `pytest` | Diff unificado e logs dos 4 scanners prontos para despacho. |
| **2.1 `auditor-architecture`** | `Model: "flash"` | [`review-architecture.md`](../../skills/review/references/review-architecture.md) | `check_arch_boundaries.py` + `check_sdd_drift.py` | `02-auditorias/audit-architecture-[slug].md` (Código nunca alterado). |
| **2.2 `auditor-security`** | `Model: "flash"` | [`review-security.md`](../../skills/review/references/review-security.md) | `scan_sinks.py` | `02-auditorias/audit-security-[slug].md` (Código nunca alterado). |
| **2.3 `auditor-quality`** | `Model: "flash"` | [`review-quality.md`](../../skills/review/references/review-quality.md) | `ast_complexity.py` ($V(G) \le 10$) | `02-auditorias/audit-quality-[slug].md` (Código nunca alterado). |
| **2.4 `auditor-performance`** | `Model: "flash"` | [`review-performance.md`](../../skills/review/references/review-performance.md) | `ast_complexity.py` (Heurísticas Big-O) | `02-auditorias/audit-performance-[slug].md` (Código nunca alterado). |
| **2.5 `auditor-resilience`** | `Model: "flash"` | [`review-resilience.md`](../../skills/review/references/review-resilience.md) | Contratos de erro/timeout do SDD | `02-auditorias/audit-resilience-[slug].md` (Código nunca alterado). |
| **Step 3 & 4: Orquestrador (Reduce)** | Sessão Ativa | `SKILL.md` | 5 relatórios de auditoria concluídos | Atualiza `dod-[slug].md`; se Mode B (`--fix`), aplica fixes cirúrgicos e roda `pytest -v`. |
