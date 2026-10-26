# Skill: Redação Técnica & Documentação Viva (`docs`)

A skill **`docs`** atua na **Fase 5 (`/docs`)**, orientando a geração e sincronização contínua da documentação técnica da funcionalidade recém-auditada. Ela estabelece padrões rígidos para READMEs (raiz e módulos locais) e docstrings de código de produção, garantindo rastreabilidade bidirecional com o Obsidian Vault e comandos operacionais reais validados contra os manifestos do projeto.

---

## ⛔ Restrições e Guardrails de Redação Técnica

```mermaid
flowchart TD
    D1["<b>1. Zero Comandos Fictícios ou Obsoletos</b><br/>Comandos de execução e teste validados contra manifests reais"]
    D2["<b>2. Nunca Alterar Lógica de Produção</b><br/>Intervenções restritas a docstrings, comentários e anotações de tipo"]
    D3["<b>3. Rastreabilidade Bidirecional Obsidian</b><br/>Inclusão obrigatória de Ref: Obsidian note [[sdd-[slug]]]"]
    D4["<b>4. Diagramação Segura Mermaid</b><br/>Labels entre aspas duplas (node[\"Texto\"]) em todos os diagramas"]
    
    D1 --> D2 --> D3 --> D4
```

---

### 1. Validação de Comandos Reais
* Todos os comandos de instalação de dependências, execução de servidores locais e suítes de teste inseridos na documentação devem ser checados e validados contra os manifestos ativos:
  * `package.json` (`scripts`), `pyproject.toml` (`tool.poetry.scripts` ou `project.scripts`), `Makefile`, etc.
* Elimina a ocorrência de tutoriais com comandos quebrados ou inventados pela IA.

---

### 2. Rastreabilidade com a Segunda Mente (Obsidian)
* Toda nova classe, função pública ou use case introduzido pela feature deve receber uma docstring estruturada contendo a referência explícita para o blueprint de concepção gravado no Vault:
  ```python
  def process_transfer(source_acc: str, target_acc: str, amount: Decimal) -> TransferReceipt:
      """
      Executa a transferência atômica entre contas com verificação de limites.
      
      Ref: Obsidian note [[sdd-transferencias-pix]]
      """
  ```

---

### 3. Padrões de Templates de Documentação
* **README Raiz (`resources/template_readme_root.md`):** Vitrine pública do projeto, visão de negócio, onboarding rápido de 5 minutos e links para manuais técnicos.
* **README de Módulo Local (`resources/template_readme_local.md`):** Especificação atômica do módulo contendo objetivo, arquitetura interna, dependências consumidas, contratos de API pública e instruções de teste.

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/docs/SKILL.md`](../../skills/docs/SKILL.md)
* **Template do README Raiz:** [`skills/docs/resources/template_readme_root.md`](../../skills/docs/resources/doc-template.md)
* **Template do README Local:** [`skills/docs/resources/template_readme_local.md`](../../skills/docs/resources/doc-template.md)
