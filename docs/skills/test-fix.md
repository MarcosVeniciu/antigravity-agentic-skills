# Skill: Depuração Reativa & Correção Cirúrgica de Testes (`test-fix`)

A skill **`test-fix`** atua como o mecanismo de depuração cirúrgica de suporte para falhas de testes unitários ou de integração durante a **Fase 2 (`/implement`)** e a **Fase 3 (`/refactor`)**. Ela orienta a IA a ingerir logs de erro e stack traces do terminal, isolar a causa raiz em uma única sentença e aplicar a menor intervenção possível no código de produção para restabelecer o status verde sem desfigurar a suíte de testes.

---

## ⛔ Regras Estritas de Blindagem

```mermaid
flowchart TD
    Trace["Traceback / Falha no Terminal"] --> C1["<b>1. Causa Raiz em 1 Frase</b><br/>Isolamento sintético do motivo exato do erro"]
    C1 --> C2["<b>2. Correção Mínima em Produção</b><br/>Edita apenas as linhas estritamente causadoras"]
    C2 --> C3["<b>3. Preservação de Asserções</b><br/>🚫 Terminantemente proibido alterar os asserts dos testes"]
    C3 --> C4["<b>4. Micro-Checkpoint Imediato</b><br/>Salva o progresso via git commit (checkpoint)"]
```

---

### 1. Isolamento da Causa Raiz em 1 Sentença
* Antes de propor qualquer edição de arquivo, a IA deve formular expressamente a causa raiz do problema em uma frase precisa.
* **Exemplo de Formulação:**
  * *"O `OrderService` lança `KeyError` porque o payload recebido omite o campo opcional `discount_code` durante o cálculo do subtotal."*

---

### 2. Intervenção Cirúrgica no Código de Produção
* As alterações devem se ater estritamente ao ponto de falha no código de aplicação.
* É proibido aproveitar o momento do fix para fazer refatorações amplas de código que não falhou.

---

### 3. Preservação Inegociável dos Testes
* O teste unitário é a especificação formal do comportamento do sistema.
* Mudar expectativas de teste para mascarar um defeito de implementação é considerado anti-pattern grave e violação de integridade.

---

### 4. Micro-Checkpoint Imediato
* Assim que o comando de teste no terminal retornar com 100% dos testes verdes, a skill orienta a gravação imediata do micro-checkpoint via `@git` (Modo 2).

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/test-fix/SKILL.md`](../../skills/test-fix/SKILL.md)
* **Manual de Depuração:** [`skills/test-fix/references/EXECUTION.md`](../../skills/test-fix/references/test-fix-protocol.md)
* **Template do Checklist de Diagnóstico:** [`skills/test-fix/resources/error_checklist_template.md`](../../skills/test-fix/resources/diagnostic-report-template.md)
