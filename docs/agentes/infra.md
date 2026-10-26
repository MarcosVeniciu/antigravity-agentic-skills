# Agente de Infraestrutura & Dependências (`/infra`) - Gestão Segura de Ambiente

O agente de **Infraestrutura & Dependências (`/infra`)** atua no gerenciamento seguro de arquivos de configuração, manifestos de pacotes (`package.json`, `pyproject.toml`, `requirements.txt`), contêineres Docker e variáveis de ambiente no Antigravity IDE.

Sua responsabilidade principal é assegurar que o ambiente técnico seja atualizado sem vazamento de credenciais ou degradação de compatibilidade.

---

## ⛔ Regras Invioláveis de Segurança

1. **🚫 Blindagem Absoluta contra Vazamento de Segredos:** Jamais comita arquivos `.env` reais, chaves privadas (`.pem`), tokens de API ou credenciais de banco. Todas as novas variáveis devem ser documentadas exclusivamente em `.env.example` com valores mock/placeholder.
2. **🚫 Atualizações Declarativas:** Toda adição ou remoção de pacote deve ser refletida no manifesto oficial da stack e travada no respectivo arquivo de lock (`poetry.lock`, `package-lock.json`, etc.).

---

## 🚀 Pipeline de Gestão de Infraestrutura

1. **Diagnóstico do Ambiente:** Inspeciona o estado atual dos manifestos e containers.
2. **Validação de Variáveis de Ambiente:**
   ```bash
   python skills/infra/scripts/validate_env.py
   ```
3. **Aplicação de Mudanças:** Executa a atualização de dependências ou configurações de Docker.
4. **Espelhamento em `.env.example`:** Assegura que novas variáveis necessárias estejam catalogadas sem dados sensíveis.
* 💡 **Referência Operacional:** [`skills/infra/references/infra-setup.md`](../../skills/infra/references/infra-setup.md)
* 📋 **Template de Ambiente:** [`skills/infra/resources/env-template.md`](../../skills/infra/resources/env-template.md)
* 🛠️ **Script de Validação:** [`skills/infra/scripts/validate_env.py`](../../skills/infra/scripts/validate_env.py)

---

## 🧰 Estrutura da Skill no Antigravity 2.0

* **Manifesto da Skill (`SKILL.md`):** [`skills/infra/SKILL.md`](../../skills/infra/SKILL.md)
* **Guias Operacionais (`references/`):**
  * [`infra-setup.md`](../../skills/infra/references/infra-setup.md) — Gestão segura de pacotes, contêineres e variáveis
* **Templates de Ambiente (`resources/`):**
  * [`env-template.md`](../../skills/infra/resources/env-template.md) — Modelo seguro para catalogação de variáveis em `.env.example`
* **Scripts de Validação (`scripts/`):**
  * [`validate_env.py`](../../skills/infra/scripts/validate_env.py) — Validador de integridade entre `.env` e `.env.example`
* **Exemplos Práticos (`examples/`):**
  * [`infra-example.md`](../../skills/infra/examples/infra-example.md)
