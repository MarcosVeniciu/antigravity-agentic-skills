# Skill: Especificação Comportamental BDD (`plan-bdd`)

A skill **`plan-bdd`** atua na **Fase 1 (`/plan`)**, modelando os requisitos de negócio e cenários funcionais estritamente na sintaxe pura de **Gherkin (`Given/When/Then`)**, assegurando que o comportamento esperado pelo usuário e pelo negócio seja blindado antes da criação de qualquer especificação técnica ou código.

---

## 🎯 As 3 Regras de Ouro do BDD

```mermaid
flowchart LR
    R1["<b>1. Linguagem Ubíqua</b><br/>Zero jargões de banco ou rede<br/>Foco na intenção do usuário"]
    R2["<b>2. Cobertura Essencial</b><br/>Happy Path + Unhappy Paths<br/>(Erros de validação e restrições)"]
    R3["<b>3. Fidelidade ao Escopo</b><br/>Aderência estrita à proposta<br/>aprovada no debate"]
    
    R1 --> R2 --> R3
```

---

### 1. Linguagem Ubíqua e Acessível (Sem Vazamento Técnico)
* Os cenários devem ser compreensíveis tanto por desenvolvedores quanto por analistas de negócio e Product Owners.
* **Jargões Estritamente Proibidos:** Termos como `SELECT`, `tabela`, `endpoint REST`, `payload JSON`, `HTTP 200` ou `status code 404` não devem constar nos passos Gherkin.
* **Exemplo de Tradução Correta:**
  * ❌ *Incorreto:* `When faço um POST para /api/v1/auth com JSON de credenciais`
  * ✅ *Correto:* `When informo meu e-mail e senha cadastrados e solicito o login`

---

### 2. Cobertura Abrangente (Caminhos Felizes e de Exceção)
* **Caminho Feliz (Happy Path):** Fluxos nominais em que todas as pré-condições são satisfeitas.
* **Caminhos de Exceção (Unhappy Paths):**
  * Tentativas com dados inválidos ou campos obrigatórios vazios.
  * Violações de regras de negócio (ex: tentar sacar valor superior ao saldo).
  * Tentativas de acesso a recursos não permitidos.
  * Estados conflitantes do sistema (ex: cupom expirado ou estoque esgotado).

---

### 3. Fidelidade Absoluta ao Estado Final Aprovado
* Cada cenário deve validar pontualmente os critérios de sucesso estabelecidos na proposta arquitetural aprovada na etapa de debate (`scope_proposals.md`).
* A especificação gerada é persistida no Obsidian Vault em `01-concepcao/bdd-[slug].md`.

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/plan-bdd/SKILL.md`](../../skills/plan/SKILL.md)
* **Template de BDD:** [`skills/plan-bdd/resources/template_bdd.md`](../../skills/plan/resources/plan-template.md)
* **Exemplo Prático de Referência:** [`skills/plan-bdd/examples/bdd_checkout_example.md`](../../skills/plan/references/plan-bdd.md)
