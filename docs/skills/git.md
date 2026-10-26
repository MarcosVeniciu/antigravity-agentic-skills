# Skill: Governança Git Flow e Versionamento Local (`git`)

A skill **`git`** é a autoridade central e unificada de controle de versão local no Antigravity IDE. Ela gerencia o fluxo de branches Git Flow, salvaguarda o progresso do desenvolvedor através de micro-checkpoints rápidos, consolida mudanças atômicas em commits semânticos entre chats e orquestra a finalização de releases com tags anotadas.

---

## 🔄 Os 5 Modos Operacionais

A skill opera através de 5 modos estritos, carregados sob demanda:

### Modo 1: Estratégia de Branches & Validação Git Flow
* **Momento:** Início da Fase 1 (`/plan`) ou Fase 0 (`/decompose`).
* **Regras:**
  * Impede desenvolvimento direto em branches protegidas (`main`, `master`, `develop`).
  * Valida e orienta o checkout da branch da feature:
    ```bash
    git checkout -b feature/[slug]
    ```
* **Script de Apoio:** [`skills/git/scripts/validate_branch.sh`](../../skills/plan/scripts/validate_branch.py).

---

### Modo 2: Micro-Checkpoints Locais
* **Momento:** Durante a codificação em lote da Fase 2 (`/implement`), após cada componente refatorado na Fase 3 (`/refactor`), após cada domínio auditado na Fase 4 (`/review`) ou após correções reativas (`/test-fix`).
* **Regras:**
  * Cria pontos de restauração frequentes para evitar perda de trabalho.
  * Formato da mensagem: `checkpoint([fase]): [descrição atômica]`.
  ```bash
  git add .
  git commit -m "checkpoint(implement): batch 1 - domain entities and value objects"
  ```

---

### Modo 3: Fechamento de Fase & Phase Squash Commit
* **Momento:** Ao final de cada conversa/chat de fase (Fases 1, 2, 3, 4 e 5).
* **Regras:**
  * Opcionalmente agrupa micro-checkpoints intermediários em um commit semântico limpo, narrativo e rastreável.
  * Formato no padrão Conventional Commits (`docs(...)`, `feat(...)`, `refactor(...)`, `audit(...)`).
  * Utiliza o modelo estruturado [`skills/git/resources/template_phase_commit.md`](../../skills/plan/references/plan-git.md).

---

### Modo 4: Rollback Local de Emergência (*Double-Strike*)
* **Momento:** Quando um teste falha após uma refatoração ou quando uma correção em `/test-fix` falha 2 vezes consecutivas.
* **Regras:**
  * Interrompe o loop de erros e restaura instantaneamente o repositório ao último estado funcional limpo:
    ```bash
    git reset --hard HEAD
    ```
  * Evita poluição da janela de contexto da IA com correções acumuladas defeituosas.

---

### Modo 5: Branch de Release, Tags Anotadas & Fechamento Git Flow
* **Momento:** Durante a publicação formal de release (`/release`).
* **Regras:**
  * Cria a branch `release/vX.Y.Z` a partir de `develop`.
  * Mescla as features candidatas (`git merge --no-ff feature/[slug]`).
  * Após aprovação dos testes de integração, cria a tag anotada:
    ```bash
    git tag -a v[VERSION] -m "Release v[VERSION]"
    ```
  * Mescla a release em `main` e `develop` e remove as branches temporárias.

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/git/SKILL.md`](../../skills/plan/references/plan-git.md)
* **Procedimento Detalhado dos Modos:** [`skills/git/references/EXECUTION.md`](../../skills/plan/references/plan-git.md)
* **Script de Validação:** [`skills/git/scripts/validate_branch.sh`](../../skills/plan/scripts/validate_branch.py)
* **Template de Commit de Fase:** [`skills/git/resources/template_phase_commit.md`](../../skills/plan/references/plan-git.md)
