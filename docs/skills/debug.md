# Skill: Investigação Forense de Bugs & 5 Whys (`debug`)

A skill **`debug`** atua no workflow de suporte **`/debug`**, fornecendo a metodologia de engenharia de software para diagnosticar e erradicar falhas críticas de runtime, exceções não tratadas e inconsistências de infraestrutura através da técnica interrogativa dos **5 Whys (Cinco Porquês)**.

---

## ⛔ Restrições Operacionais Rígidas

```mermaid
flowchart TD
    Bug["Falha Crítica Inesperada"] --> Pause["<b>1. Pausa Obrigatória (RequestFeedback)</b><br/>Apresentação da causa raiz em root_cause_analysis.md<br/>Zero modificação de código antes da aprovação do usuário"]
    Pause --> NoGuess["<b>2. Proibido Suposições ou Chutes</b><br/>Falta de logs ou configs exige pausa e requisição de evidências"]
    NoGuess --> Bash["<b>3. Comandos em Blocos Bash Isolados</b><br/>Instruções diagnósticas fornecidas em blocos limpos de linha única"]
    Bash --> Whys["<b>4. Aplicação dos 5 Whys</b><br/>Identificação da causa raiz sistêmica e estrutural"]
```

---

## 🔬 Metodologia dos 5 Whys (Cinco Porquês)

A análise investiga a cadeia causal regressiva para encontrar o defeito de design, em vez de aplicar correções superficiais que apenas mascaram a exceção:

1. **Por que 1 (Sintoma Direto):** Por que o servidor retornou HTTP 500?
   * *Ex: O worker abortou por `ConnectionResetError`.*
2. **Por que 2 (Mecanismo):** Por que a conexão foi resetada?
   * *Ex: O pool de conexões do banco atingiu o limite máximo de clientes simultâneos.*
3. **Por que 3 (Consumo):** Por que as conexões foram esgotadas?
   * *Ex: Uma query de relatório executada na thread de requisição ficou bloqueada por mais de 60 segundos.*
4. **Por que 4 (Governança de I/O):** Por que a query não foi interrompida?
   * *Ex: Não havia timeout de statement configurado no cliente do banco de dados.*
5. **Por que 5 (Causa Raiz Sistêmica):** Por que essa query pesada de relatório está na mesma conexão das transações OLTP?
   * *Ex: Falta de isolamento entre a réplica de leitura e a conexão de escrita.*

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/debug/SKILL.md`](../../skills/debug/SKILL.md)
* **Manual da Metodologia dos 5 Whys:** [`skills/debug/references/5_whys_framework.md`](../../skills/debug/references/debug-methodology.md)
* **Template de Causa Raiz (RCA):** [`skills/debug/resources/template_root_cause.md`](../../skills/debug/resources/rca-template.md)
