# Skill: Arquitetura Técnica & Contratos SDD (`plan-sdd`)

A skill **`plan-sdd`** atua na **Fase 1 (`/plan`)**, traduzindo os cenários funcionais de BDD em uma especificação técnica de engenharia formal (**Software Design Document - SDD**). Ela estabelece diagramas visuais protegidos em Mermaid, contratos tipados de fronteira e a matriz de impacto em arquivos antes do início do TDD.

---

## 🎯 Diretrizes Técnicas de Modelagem

```mermaid
flowchart TD
    BDD["Cenários BDD (Gherkin)"] --> M1["<b>1. Diagramação Segura Mermaid</b><br/>Rótulos entre aspas duplas: node[\"Label\"]<br/>Diagramas de Sequência e Classes"]
    M1 --> M2["<b>2. Contratos Tipados de Fronteira</b><br/>Schemas estritos (Pydantic / Zod / TS)<br/>Mocks tipados com casos de sucesso e erro"]
    M2 --> M3["<b>3. Matriz de Impacto em Arquivos</b><br/>Classificação de arquivos Criados vs Modificados<br/>Prevenção de regressões colaterais"]
    M3 --> Out["Salvo em 01-concepcao/sdd-[slug].md"]
```

---

### 1. Modelagem Visual Segura (Mermaid.js)
* **Regra Inviolável de Sintaxe:** Todo rótulo de nó, ator ou mensagem deve obrigatoriamente estar contido entre aspas duplas (ex: `A["Cliente Web"] --> B["Serviço de Autenticação (JWT)"]`). Isso elimina falhas comuns de renderização do parser Mermaid no Antigravity IDE.
* **Diagramas de Sequência:** Utilizados para mapear o fluxo de dados entre controllers, use cases, portas de repositório e gateways externos.
* **Diagramas de Classe:** Utilizados para modelar entidades de domínio, agregados e interfaces abstratas.

---

### 2. Contratos Tipados de Fronteira (Boundary Mocks)
* Especifica a tipagem rígida de entrada e saída no padrão nativo da stack:
  * **Python:** Modelos Pydantic (`BaseModel`) com validação de campo e type hints nativos.
  * **TypeScript / Node:** Schemas Zod e interfaces TypeScript exportadas.
  * **Flutter / Dart:** Classes imutáveis com construtores nomeados e serializadores tipados.
* Define previamente as exceções tipadas de domínio que devem ser lançadas sob entradas inválidas.

---

### 3. Matriz de Impacto em Arquivos
* Identifica previamente todos os arquivos que serão afetados pela implementação da feature:
  * **Aditivos ([NEW]):** Novos arquivos que serão criados (baixo risco de regressão).
  * **Mutativos ([MODIFY]):** Arquivos legados existentes que sofrerão intervenção (alto risco de regressão; exige testes de salvaguarda).

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/plan-sdd/SKILL.md`](../../skills/plan/SKILL.md)
* **Manual de Modelagem SDD:** [`skills/plan-sdd/references/sdd_execution.md`](../../skills/plan/references/plan-sdd.md)
* **Template de SDD:** [`skills/plan-sdd/resources/template_sdd.md`](../../skills/plan/resources/plan-template.md)
* **Exemplo Prático de Arquitetura:** [`skills/plan-sdd/examples/sdd_checkout_example.md`](../../skills/plan/examples/plan-example.md)
* **Script de Validação de Contratos:** [`skills/plan-sdd/scripts/validate_sdd_contracts.py`](../../skills/plan/scripts/validate_sdd_contracts.py)
