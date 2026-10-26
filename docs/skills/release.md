# Skill: Gestão de Release & SemVer Cumulativo (`release`)

A skill **`release`** atua no pipeline de publicação **`/release`**, sendo a autoridade técnica responsável pelo cálculo do incremento de versão de acordo com a especificação **SemVer 2.0.0** e pela consolidação contínua do histórico de alterações no `CHANGELOG.md` e no Obsidian Vault.

---

## 🎯 Cálculo Semântico de Versão (SemVer 2.0.0)

A skill inspeciona o acumulado de commits semânticos presentes no lote de features mescladas na branch de release:

```mermaid
flowchart TD
    Commits["Commits Semânticos das Features Mescladas"] --> CheckMajor{"Contém BREAKING CHANGE ou<br/>quebra de contrato público?"}
    CheckMajor --"Sim"--> Major["<b>MAJOR Bump (vX+1.0.0)</b><br/>Incompatibilidade retroativa"]
    CheckMajor --"Não"--> CheckMinor{"Contém commits de nova<br/>funcionalidade (feat:)?"}
    CheckMinor --"Sim"--> Minor["<b>MINOR Bump (vX.Y+1.0)</b><br/>Novos recursos retrocompatíveis"]
    CheckMinor --"Não"--> Patch["<b>PATCH Bump (vX.Y.Z+1)</b><br/>Apenas correções e refatorações (fix, perf)"]
```

---

## 📝 Consolidação do Changelog

1. **Agrupamento Padronizado por Seção:**
   * 🚀 **Novas Funcionalidades (Features):** Commits com prefixo `feat:`.
   * 🐛 **Correções de Bugs (Bug Fixes):** Commits com prefixo `fix:`.
   * ⚡ **Performance & Refatoração:** Commits com prefixos `perf:` e `refactor:`.
   * ⚠️ **Alterações Quebrantes (Breaking Changes):** Detalhes da quebra e instrução de migração.
2. **Atualização Cumulativa na Raiz:**
   * Adiciona o novo bloco de versão no topo do arquivo [`CHANGELOG.md`](../../CHANGELOG.md) do repositório, preservando integralmente o histórico das releases passadas.
3. **Persistência na Segunda Mente:**
   * Salva uma cópia imutável em `03-releases/changelog-v[VERSION].md` no Obsidian Vault com tags `#phase/release` e metadados de auditoria.

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/release/SKILL.md`](../../skills/release/SKILL.md)
* **Matriz de Regras SemVer:** [`skills/release/references/semver_rules.md`](../../skills/release/references/release-checklist.md)
* **Template do Changelog:** [`skills/release/resources/template_changelog.md`](../../skills/release/resources/release-template.md)
