# Skill: Auditoria Arquitetural (`review-architecture`) - Isolamento de Camadas

A skill **`review-architecture`** audita alterações de código sob a perspectiva de arquitetura de software, desacoplamento, inversão de dependência (DIP) e estrito isolamento de camadas de negócio (Clean Architecture / Hexagonal / DDD).

---

## ⚡ Estratégia Script-First com `check_arch_boundaries.py`

A auditoria arquitetural inicia obrigatoriamente pela execução do script de análise estática de fronteiras:

```bash
python skills/review-architecture/scripts/check_arch_boundaries.py <arquivos_alterados>
```

### O que o Script Valida:
* **Camada de Domínio Pura:** Impede que arquivos contidos em pastas como `domain/`, `entities/` ou `use_cases/` importem bibliotecas de infraestrutura, banco de dados, clientes HTTP ou frameworks web.
* **Suporte Poliglota:**
  * **Python:** Bloqueia imports de `requests`, `boto3`, `sqlalchemy`, `flask`, `fastapi`, `django`, etc.
  * **TypeScript / Node:** Bloqueia imports de `axios`, `express`, `react`, `next`, `typeorm`, `prisma`, etc.
  * **Flutter / Dart:** Bloqueia dependências de `package:flutter/`, `package:http/`, `dart:io`, etc. dentro do domínio puro.

---

## 🎯 Pilares da Revisão Manual Orientada
Após avaliar o relatório do script, o agente foca a leitura de código nos seguintes princípios:

1. **Vazamento de Infraestrutura:** Garantir que entidades e use cases dependam exclusivamente de abstrações (Interfaces/Ports).
2. **Inversão de Dependência (DIP):** Exigir injeção de dependências no construtor (`__init__` / `constructor`) em vez de instanciar clientes de banco ou APIs dentro de métodos.
3. **Decomposição de God Classes:** Quebrar classes com múltiplas responsabilidades em serviços coesos e especializados.
4. **Imutabilidade de Argumentos:** Evitar mutações em coleções recebidas criando cópias defensivas.

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/review-architecture/SKILL.md`](../../skills/review/SKILL.md)
* **Checklist Detalhado:** [`skills/review-architecture/references/checklist_architecture.md`](../../skills/review/references/review-architecture.md)
* **Script de Fronteiras:** [`skills/review-architecture/scripts/check_arch_boundaries.py`](../../skills/review/scripts/check_arch_boundaries.py)
* **Template de Relatório:** [`skills/review-architecture/resources/template_architecture.md`](../../skills/review/resources/audit-report-template.md)
