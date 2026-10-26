# Skill: Testes de Integração e E2E (`test-integration`) - Validação Consolidada

A skill **`test-integration`** orquestra e executa suítes de testes de integração e ponta-a-ponta (E2E) no ambiente consolidado da branch de release. Ela assegura que múltiplos módulos e contratos coexistam sem quebras, suportando validações de resiliência, vetores web e concorrência real sob carga.

---

## 🏗️ Padrão de Estágios com Console Banners (9 Estágios)

A execução da suíte de integração emite banners estruturados no console para rastreabilidade matemática do pipeline de liberação:

```text
[STAGE 1] E2E HAPPY PATH: Fluxo Nominal Completo (Login -> Cadastro -> Execução -> Persistência)
[STAGE 2] UNHAPPY PATH: Tentativa de Acesso Não Autenticado (403 Forbidden)
[STAGE 3] UNHAPPY PATH: Credenciais Inválidas / Falha de Autenticação (401 Unauthorized)
[STAGE 4] UNHAPPY PATH: Rejeição de Entidade Duplicada (409 Conflict)
[STAGE 5] UNHAPPY PATH: Falha de Validação de Schema (422 Unprocessable Entity)
[STAGE 6] UNHAPPY PATH: Resiliência & Degradação Graciosa sob Falha Externa (HTTP 200 via Fallback)
[STAGE 7] SECURITY: Validação de Proteção Anti-CSRF (403 em requisições de mutação sem token)
[STAGE 8] SECURITY: Neutralização de Open Redirect & SSRF (Bloqueio / fallback para rota interna segura)
[STAGE 9] CONCURRENCY: Estresse Concorrente de Carga e Atomicidade de Estado (Zero corrupção TOCTOU)
```

---

## 🔒 Detalhamento dos Estágios de Segurança e Concorrência

### Stage 7: Verificação Anti-CSRF
Dispara requisições `POST`, `PUT` ou `DELETE` contra rotas de mutação de estado omitindo o cabeçalho anti-CSRF ou token correspondente:
* **Asserção:** O servidor de teste deve responder estritamente com status `403 Forbidden`.

### Stage 8: Neutralização de Redirecionamento Aberto (Open Redirect)
Envia requisições para rotas de autenticação ou navegação com destinos arbitrários externos (ex: `?next=https://evil-phishing.com`):
* **Asserção:** O cabeçalho de resposta `Location` deve apontar para uma rota interna padrão (ex: `/` ou `/dashboard`), rejeitando domínios fora da allowlist.

### Stage 9: Concorrência e Atomicidade Real sob Carga
Dispara rajadas paralelas de requisições HTTP reais contra a API (ex: 20 a 50 clientes simultâneos tentando utilizar o mesmo cupom ou resgatar o último item em estoque):
* **Asserção:** O banco de dados ou estado compartilhado deve preservar atomicidade estrita: apenas 1 transação é confirmada e as demais recebem status de erro de conflito (`409` ou `422`).

---

## 🌐 Suporte Poliglota para Runners
* **Python:** Utiliza `pytest -s` com fixtures de cliente HTTP (`TestClient`) e `concurrent.futures.ThreadPoolExecutor`.
* **Node.js / TypeScript:** Utiliza `vitest`/`jest` com `supertest` e `Promise.allSettled()`.
* **Flutter / Dart:** Utiliza `flutter_test` / `integration_test` com `Future.wait()`.

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/test-integration/SKILL.md`](../../skills/release/SKILL.md)
* **Padrões de Runner E2E:** [`skills/test-integration/references/e2e_runner_pattern.md`](../../skills/release/references/release-checklist.md)
* **Template de Relatório de Integração:** [`skills/test-integration/resources/template_integration_log.md`](../../skills/release/resources/release-template.md)
