# Skill: Infraestrutura & Dependências Seguras (`infra`)

A skill **`infra`** atua no workflow de suporte **`/infra`**, gerenciando manifestos de dependências de pacotes, contêineres Docker e variáveis de ambiente com estrita observância a guardrails de segurança e prevenção contra vazamento de credenciais.

---

## ⛔ Restrições Operacionais Rígidas

```mermaid
flowchart TD
    I1["<b>1. Sem Upgrades Cegos (No Blind Upgrades)</b><br/>Modifica apenas as dependências estritamente necessárias"]
    I2["<b>2. Zero Segredos em Código (No Hardcoded Secrets)</b><br/>Proibido credenciais, chaves ou tokens em arquivos rastreados"]
    I3["<b>3. Escopo Estrito de Infraestrutura</b><br/>Não altera lógica de aplicação ou regras de negócio"]
    I4["<b>4. Sincronização Obrigatória com .env.example</b><br/>Novas variáveis exigem placeholders seguros e documentados"]
    
    I1 --> I2 --> I3 --> I4
```

---

## 📋 Checklist de Execução e Validação

1. **Sincronização de Variáveis de Ambiente (`.env.example`):**
   * Toda variável consumida pelo sistema deve ter sua chave espelhada no arquivo `.env.example` com valores mock ilustrativos (ex: `DATABASE_URL=postgres://user:pass@localhost:5432/app_db`).
   * Arquivos reais de segredo (`.env`, `.env.local`, `*.pem`) devem estar obrigatoriamente declarados no `.gitignore`.
2. **Validação de Sintaxe e Integridade dos Manifestos:**
   * Executa linters e parsers para validar JSON/YAML e Dockerfiles antes de concluir a intervenção.
3. **Handover de Retorno:**
   * Após a conclusão das alterações de infraestrutura, orienta a continuação do fluxo principal:
   > **[NEXT STEP]** ➡️ *"⚙️ Configurações de infraestrutura e dependências atualizadas com sucesso! Prossiga com o ciclo de desenvolvimento via `/implement` ou valide alterações utilizando `/test-fix`."*

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/infra/SKILL.md`](../../skills/infra/SKILL.md)
