# Skill: Decomposição de Épicos & Fatiamento Evolutivo (`plan-decompose`)

A skill **`plan-decompose`** atua na **Fase 0 (`/decompose`)**, decompondo iniciativas complexas, migrações de infraestrutura e demandas amplas de produto em uma sequência ordenada e independente de sub-features (fatias verticais), prevenindo "Mega-PRs" e saturação da janela de contexto da LLM.

---

## 🎯 As 3 Regras de Ouro do Fatiamento Evolutivo

```mermaid
flowchart TD
    R1["<b>1. Monotonicidade Arquitetural</b><br/>Sub-feature N+1 consome e estende Sub-feature N<br/>Zero retrabalho cíclico ou quebra de testes passados"]
    R2["<b>2. Contratos & Mocks Primeiro</b><br/>Interfaces (Ports) e Repositórios Mock em memória na Sub-feature 1<br/>Banco de dados ou rede real apenas nas fatias subsequentes"]
    R3["<b>3. Calibração de Ciclo</b><br/>Cada fatia dimensionada estritamente para caber<br/>em 1 conversa de desenvolvimento (Fases 1 a 5)"]
    
    R1 --> R2 --> R3
```

---

### 1. Monotonicidade Arquitetural (Sem Retrabalho Destrutivo)
* Cada sub-feature fatiada constrói uma camada sólida e utilizável sobre a qual a próxima fatia se apoia.
* **Anti-Pattern Evitado:** Fatiamento horizontal ingênuo (ex: "fazer todo o banco de dados na fatia 1, todas as telas na fatia 2"), onde a fatia 2 frequentemente obriga a reescrever o código da fatia 1.

---

### 2. Contratos e Mocks Primeiro (Isolamento de Fronteiras)
* Quando a iniciativa envolve integração com bancos de dados, mensageria externa ou APIs de terceiros, a **Sub-feature 1** define estritamente:
  * A interface/contrato de abstração (`IRepository` ou `IClient`).
  * A implementação mock em memória com fixtures de dados simulados.
  * Os casos de uso consumindo essa abstração.
* A persistência real (PostgreSQL, Redis, RabbitMQ) é introduzida como uma fatia complementar e intercambiável posteriormente.

---

### 3. Calibração de Ciclo por Sub-Feature
* A fatia vertical é calibrada para que seu ciclo completo de vida (BDD $\rightarrow$ TDD $\rightarrow$ Refatoração $\rightarrow$ Auditorias $\rightarrow$ Documentação) seja executado confortavelmente dentro dos limites de uma sessão atômica de chat.

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/plan-decompose/SKILL.md`](../../skills/decompose/SKILL.md)
* **Diretrizes Técnicas de Fatiamento:** [`skills/plan-decompose/references/slicing_rules.md`](../../skills/decompose/references/decompose-protocol.md)
* **Template do Épico:** [`skills/plan-decompose/resources/template_epic.md`](../../skills/decompose/resources/task-template.md)
* **Exemplo Prático de Decomposição:** [`skills/plan-decompose/examples/epic_decomposition_example.md`](../../skills/decompose/examples/decompose-example.md)
