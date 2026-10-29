# Arquitetura da Skill `/infra` (Infrastructure & Environment Governance — Direct Orchestrator Execution)

> [!IMPORTANT]
> **Documento Exclusivo de Engenharia e Manutenção da Skill `/infra`:**
> Este documento reside em `doc/infra/README.md` e detalha a especificação arquitetural, pipeline e guardrails da skill `/infra`. Ele **não** é instalado em `~/.gemini/config/skills/` nem em `.agents/skills/`, garantindo **zero poluição de contexto** para o agente em produção.

---

## 1. O Problema Resolvido: Dependências Caóticas e Vazamento de Segredos

Alterações de infraestrutura e dependências frequentemente introduzem riscos críticos ao ecossistema de software:
1. **Upgrades Cegos e Quebras Transitivas:** Execuções indiscriminadas de comandos como `pip install --upgrade *` ou `npm update` introduzem breaking changes não planejadas em dependências transitivas.
2. **Vazamento Acidental de Credenciais (*Secret Leakage*):** O commit de arquivos `.env` ou a inserção de chaves reais em arquivos de exemplo (`.env.example`) expõe senhas de banco de dados, chaves de API (`sk_live_...`) e tokens JWT.
3. **Divergência entre Ambientes (*Environment Drift*):** Desenvolvedores adicionam variáveis consumidas no código sem atualizar o `.env.example`, gerando falhas catastróficas em pipelines de CI/CD ou ambientes de outros engenheiros.
4. **Contaminação de Código de Aplicação:** Operações de infraestrutura que inadvertidamente alteram lógicas de negócio em `src/`, quebrando o isolamento de camadas.

A skill **`/infra`** governa manifests de pacotes, configurações de containers Docker e variáveis de ambiente com contenção absoluta de credenciais e validação sintática automatizada via script multiplataforma determinístico.

---

## 2. Decisão Arquitetural: Execução 100% no Orquestrador Principal (Zero Subagents)

Assim como a skill `/test-fix`, a skill `/infra` opera **exclusivamente no Orquestrador Principal, sem instanciar subagentes**.

### Justificativa de Engenharia de Contexto:
- **Zero Boot Token Overhead:** A inicialização de um subagent consome entre 3.000 e 8.000 tokens (system prompt, catálogo de ferramentas e esquemas). Para adicionar uma biblioteca pontual ao `pyproject.toml` ou validar um `.env.example`, o custo de boot superaria o payload útil da própria operação.
- **Operações Determinísticas e Bounded:** Edições de infraestrutura são operações de escopo estrito, pontual e passo único (ler manifesto, adicionar dependência pinada, rodar linter de ambiente). Não há necessidade de árvores de raciocínio divergentes ou exploração aberta.
- **Disponibilidade Imediata no Contexto Ativo:** Quando uma nova dependência é instalada pelo `/infra`, o Orquestrador Principal precisa desse conhecimento imediatamente em seu fluxo de trabalho para prosseguir com a implementação (`/implement`) ou correção de testes (`/test-fix`), sem a necessidade de trocas de mensagens assíncronas entre sessões.

```mermaid
flowchart TD
    subgraph InfraPipeline["Skill /infra (100% Main Orchestrator — Zero Subagents)"]
        S1["<b>Step 1: Descoberta de Manifestos</b><br/>Identifica pyproject.toml, package.json,<br/>Dockerfile, docker-compose.yml"]
        S2["<b>Step 2: Atualização Cirúrgica de Manifestos</b><br/>Pinning estrito de dependências<br/>Dockerfile multi-stage e non-root USER"]
        S3["<b>Step 3: Sincronização & Secret Containment</b><br/>Atualiza .env.example com mocks seguros<br/>Aspas obrigatórias para valores com espaços"]
        S4["<b>Step 4: Validação CLI Determinística</b><br/>Executa python validate_env.py<br/>0 erros de sintaxe, paridade e segredos"]
        Gate{"validate_env.py aprovado?"}
        Fix["Ajusta placeholders ou aspas"]
        Handover["<b>Handover para /implement ou /test-fix</b><br/>Ambiente íntegro e seguro"]
    end

    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> Gate
    Gate -->|"Não (Erros Detectados)"| Fix
    Fix --> S4
    Gate -->|"Sim (100% Conforme)"| Handover
```

---

## 3. Matriz Operacional e Invariantes da Skill `/infra`

| Propriedade | Diretriz Arquitetural |
| :--- | :--- |
| **Ambiente de Execução** | **Orquestrador Principal (Sessão Ativa)** |
| **Uso de Subagentes** | **Nenhum (0 subagentes)** para evitar consumo excessivo de boot tokens |
| **Escopo Permitido** | Arquivos de manifesto (`pyproject.toml`, `package.json`, `Cargo.toml`), containers (`Dockerfile`, `docker-compose.yml`) e `.env.example` |
| **Isolamento de Código** | **Estritamente proibido** alterar regras de negócio, serviços ou entidades de domínio em `src/` |
| **Upgrades de Biblioteca** | **Zero upgrades cegos:** apenas pacotes estritamente necessários para o objetivo imediato |
| **Contenção de Segredos** | Credenciais reais nunca são commitadas; `.env` deve constar no `.gitignore` |
| **Validador Obrigatório** | Script determinístico multiplataforma [`validate_env.py`](../../skills/infra/scripts/validate_env.py) |

---

## 4. O Pipeline em 4 Passos

### 4.1. Step 1: Environment Diagnostics & Manifest Discovery
- Realiza a varredura inicial no repositório para mapear os arquivos gerenciadores do ecossistema:
  - Python: `pyproject.toml`, `requirements.txt`, `poetry.lock`.
  - Node / TypeScript: `package.json`, `package-lock.json`, `pnpm-lock.yaml`.
  - Rust / Go: `Cargo.toml`, `go.mod`.
  - Containers: `Dockerfile`, `docker-compose.yml`, `.dockerignore`.
- Consulta convenções do repositório em `00-core-rules/conventions.md` via `@obsidian` se aplicável.

### 4.2. Step 2: Manifest & Container Configuration Validation
- Aplica adição cirúrgica e com versões fixadas (*pinned versions*):
  - Python: `poetry add <pacote>` ou inclusão explícita com versão fixa no `pyproject.toml`.
  - Node: `npm install --save-exact <pacote>`.
- Higiene e segurança de containers Docker:
  - Uso de *multi-stage builds* separando ambiente de compilação da imagem de produção final.
  - Execução sob usuário sem privilégios (`USER appuser`).
  - Imagens base com tags imutáveis e enxutas (`python:3.11-slim`, `node:20-alpine`).
  - Garantia de que `.dockerignore` exclui `.git`, `.env` e artefatos de testes.

### 4.3. Step 3: Environment Synchronization & Secret Containment
- Se a nova capacidade exige novas variáveis de configuração, o `.env.example` é atualizado segundo [`resources/env-template.md`](../../skills/infra/resources/env-template.md).
- **As Três Regras de Ouro de Variáveis de Ambiente:**
  1. **Nunca commitar o `.env` real:** O arquivo `.env` deve permanecer isolado no ambiente local e blindado pelo `.gitignore`.
  2. **Placeholders Descritivos e Seguros:** No `.env.example`, todo valor sensível deve usar exemplos seguros (ex.: `DATABASE_URL=postgresql://user:password@localhost:5432/app_db`).
  3. **Aspas em Valores Complexos:** Valores contendo espaços ou caracteres especiais devem obrigatoriamente estar entre aspas duplas.

### 4.4. Step 4: CLI Validation & Handover
- Execução do validador determinístico Python:
  ```bash
  python skills/infra/scripts/validate_env.py .env.example
  ```
- Para verificação de consistência local entre o arquivo de desenvolvimento e o exemplo:
  ```bash
  python skills/infra/scripts/validate_env.py --env .env --example .env.example
  ```
- O validador atesta:
  - Formato sintático válido de cada linha (`KEY=VALUE`).
  - Paridade de chaves entre `.env` e `.env.example`.
  - Ausência de padrões heurísticos de segredos expostos (`sk_live_`, `ghp_`, tokens JWT, senhas reais).
- Handover imediato para retomar `/implement` ou testar via `/test-fix`.

---

## 5. O Script Determinístico `validate_env.py`

Localizado em [`skills/infra/scripts/validate_env.py`](../../skills/infra/scripts/validate_env.py), o script atua como o gatekeeper de infraestrutura:
- Converteu e unificou regras legadas em um utilitário multiplataforma nativo em Python (sem dependência de comandos Bash como `grep` ou `sed`).
- Analisa expressões regulares para detectar chaves reais de provedores (AWS, OpenAI, GitHub, Stripe, certificados privados).
- Garante conformidade de saída com exit codes determinísticos (0 para conformidade estrita, diferente de 0 para violações).

---

## 6. Referências e Recursos Acoplados

- [`references/infra-setup.md`](../../skills/infra/references/infra-setup.md) — Guia aprofundado de setup seguro de containers e manifests de dependências.
- [`resources/env-template.md`](../../skills/infra/resources/env-template.md) — Template padronizado e documentado para arquivos `.env.example`.
- [`scripts/validate_env.py`](../../skills/infra/scripts/validate_env.py) — Script linter determinístico de variáveis e credenciais.
- [`examples/infra-example.md`](../../skills/infra/examples/infra-example.md) — Demonstração passo a passo de adição de dependência e sanitização de variáveis.
