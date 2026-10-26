# Agente de Implementação TDD (`/implement`) - Desenvolvimento Iterativo em Lotes (Fase 2)

O agente de **Implementação TDD** atua na **Fase 2 (Chat 2)** do ciclo de vida da feature no Antigravity IDE. Sua responsabilidade é conduzir a construção do software lote por lote (*context batches*), executando o ciclo completo Red-Green-Blue (com micro-refatoração em nível de lote), suítes unitárias atômicas, código de produção estritamente suficiente e micro-checkpoints no Git.

---

## 🚀 Pipeline de Execução em 3 Etapas

```mermaid
flowchart TD
    P1["Etapa 1: Planejamento de Lotes de Contexto<br/><i>Referência: tdd-test.md / tdd-code.md</i>"] --> A1{"Plano Aprovado?<br/>(RequestFeedback)"}
    A1 --"Ajustes"--> P1
    A1 --"Aprovado (Proceed)"--> Loop["<b>Etapa 2: Loop TDD Red-Green-Blue por Lote</b>"]
    
    subgraph TDD_Loop ["Para cada Lote no task_list.md"]
        T1["1. Escrever Testes AAA (Red Phase)<br/><i>Referência: tdd-test.md</i>"] --> T2["2. Escrever Código Mínimo SOLID (Green Phase)<br/><i>Referência: tdd-code.md</i>"]
        T2 --> T3["3. Micro-Refatorar Componente Local (Blue Phase)<br/><i>Referência: tdd-refactor.md</i>"]
        T3 --> T4["4. Executar Suíte de Testes (Terminal)"]
        T4 --> Pass{"Passou?"}
        Pass --"Falha"--> Fix["Correção Cirúrgica (Root Cause)<br/><i>Referência: tdd-test.md / /test-fix</i>"]
        Fix --> T4
        Pass --"100% Verde"--> Log["Atualizar Linha do Tempo no DoD<br/><i>Referência: tdd-dod.md</i>"]
        Log --> CP["Salvar Micro-Checkpoint<br/><i>Referência: tdd-git.md</i>"]
    end
    
    Loop --> TDD_Loop
    TDD_Loop --> NextBatch{"Mais lotes pendentes?"}
    NextBatch --"Sim"--> TDD_Loop
    NextBatch --"Não (100% Concluído)"--> E3["Etapa 3: Conclusão & Handover de Fase<br/><i>Referência: tdd-git.md</i>"]
    E3 --> NextChat["<b>[NEXT STEP]</b> ➡️ Recomenda Chat 3 (/refactor)"]
```

---

### Etapa 1: Planejamento de Lotes de Contexto Dependentes
1. **Leitura dos Artefatos de Concepção:** Lê as especificações em `01-concepcao/bdd-[slug].md` e `01-concepcao/sdd-[slug].md`.
2. **Decomposição em Lotes Dependentes:**
   * **Lote 1:** Entidades de domínio, interfaces base e contratos tipados (zero dependências externas).
   * **Lotes Intermediários:** Casos de uso, regras de validação e serviços de aplicação com mocks de fronteira.
   * **Lote Final:** Rotas/controllers, adaptadores e orquestração completa.
3. **Geração dos Artefatos:** Emite `implementation_plan.md` e `task_list.md` com `RequestFeedback: true`.
4. **Portão de Entrada:** Inicia a codificação apenas após a aprovação explícita do usuário (ou clique em **Proceed**).
* 💡 **Referência Operacional:** [`skills/implement/references/tdd-test.md`](../../skills/implement/references/tdd-test.md) e [`tdd-code.md`](../../skills/implement/references/tdd-code.md)

---

### Etapa 2: Loop TDD Red-Green-Blue por Lote de Contexto
Para cada lote planejado no `task_list.md`:
1. **Fase Vermelha (Red Phase - Testes Unitários AAA):**
   * Escreve testes atômicos seguindo o padrão Arrange-Act-Assert.
   * Aplica isolamento estrito via mocks em memória (sem acesso a banco real ou chamadas de rede externas).
   * Cobre 6 dimensões de teste: Caminho Feliz, Bordas, Erros de Domínio, Resiliência, Concorrência e Fronteiras de Segurança (Shift-Left).
   * 💡 **Referência:** [`skills/implement/references/tdd-test.md`](../../skills/implement/references/tdd-test.md)
2. **Fase Verde (Green Phase - Código Mínimo SOLID):**
   * Escreve estritamente o código de produção necessário para fazer a suíte passar (*"Make it Work"*).
   * Aplica anotações de tipo completas (*strict type hints*).
   * Caso haja desvio justificado do blueprint do SDD, registra imediatamente o pivô arquitetural em `02-auditorias/pivots-[slug].md`.
   * 💡 **Referência:** [`skills/implement/references/tdd-code.md`](../../skills/implement/references/tdd-code.md)
3. **Fase Azul (Blue Phase - Micro-Refatoração em Lote):**
   * Limpeza cirúrgica **apenas do componente/classe recém-criado no lote atual**: renomeação clara de variáveis/métodos, eliminação de duplicação local imediata e ajustes de tipagem.
   * 💡 **Referência:** [`skills/implement/references/tdd-refactor.md`](../../skills/implement/references/tdd-refactor.md)
4. **Execução no Terminal & Depuração Reativa:**
   * Executa o comando de teste no terminal (`pytest`, `npm test`, etc.).
   * Se houver falha, isola a causa raiz sem alterar os testes. Na 3ª falha consecutiva, aplica a regra Double-Strike (`git reset --hard HEAD`).
5. **Governança do Lote (DoD e Micro-Checkpoint):**
   * Marca o lote concluído em `task_list.md` (`[x]`).
   * Apenda a entrada histórica na seção `## 2. Linha do Tempo de Desenvolvimento` em `01-concepcao/dod-[slug].md`.
   * Salva o micro-checkpoint no repositório:
     ```bash
     git add .
     git commit -m "checkpoint(implement): batch [N] - [description]"
     ```
   * 💡 **Referências:** [`skills/implement/references/tdd-dod.md`](../../skills/implement/references/tdd-dod.md) e [`skills/implement/references/tdd-git.md`](../../skills/implement/references/tdd-git.md)

---

### Etapa 3: Conclusão da Fase 2 & Handover
* Com 100% dos lotes finalizados e a suíte de testes unitários 100% verde:
  * Registra o checkpoint final da fase.
  * Emite a diretriz de transição de fase:
    > **[NEXT STEP]** ➡️ *"💻 Fase 2 (TDD) concluída com 100% dos testes unitários passando verde! Abra um **NOVO CHAT (Chat 3)** e execute `/refactor` para consolidar o design com princípios Clean Code e SOLID em todo o diff."*

---

## 🧰 Estrutura da Skill no Antigravity 2.0

* **Manifesto da Skill (`SKILL.md`):** [`skills/implement/SKILL.md`](../../skills/implement/SKILL.md)
* **Guias Operacionais (`references/`):**
  * [`tdd-test.md`](../../skills/implement/references/tdd-test.md) — Red Phase AAA, mocks e dimensões de teste
  * [`tdd-code.md`](../../skills/implement/references/tdd-code.md) — Green Phase SOLID mínima e tipagem estrita
  * [`tdd-refactor.md`](../../skills/implement/references/tdd-refactor.md) — Blue Phase: micro-refatoração por lote
  * [`tdd-dod.md`](../../skills/implement/references/tdd-dod.md) — Linha do tempo e registros no Living DoD
  * [`tdd-git.md`](../../skills/implement/references/tdd-git.md) — Micro-checkpoints e rollback do duplo golpe
* **Templates de Teste & Código (`resources/`):**
  * [`test-template.py`](../../skills/implement/resources/test-template.py)
  * [`code-template.py`](../../skills/implement/resources/code-template.py)
* **Exemplos Práticos (`examples/`):**
  * [`tdd-example.md`](../../skills/implement/examples/tdd-example.md)
