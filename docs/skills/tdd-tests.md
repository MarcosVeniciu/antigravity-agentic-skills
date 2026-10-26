# Skill: Testes Unitários TDD (`tdd-tests`) - Shift-Left de Segurança e Concorrência

A skill **`tdd-tests`** atua na **Fase Vermelha (Red Phase)** do loop de TDD. Ela é responsável por escrever suítes de testes unitários atômicos e isolados seguindo o padrão rigoroso **Arrange-Act-Assert (AAA)** antes da criação de qualquer código de produção.

Com a modernização recente, a skill adota o princípio de **Shift-Left**, garantindo que requisitos de concorrência e segurança nasçam testados e validados no nível unitário.

---

## 🎯 Matriz de Cobertura Obrigatória (6 Dimensões)

Para cada lote de contexto (*context batch*), os testes unitários devem cobrir:

1. **Caminho Feliz (Happy Path):** Fluxos nominais de execução e estados de retorno esperados.
2. **Casos de Borda (Edge Cases):** Limites numéricos (0, `MAX_INT`), strings vazias, valores nulos e coleções vazias.
3. **Erros e Exceções de Domínio:** Lançamento de exceções tipadas de negócio sob entradas inválidas.
4. **Resiliência e Performance:** Limiares de tempo de execução e comportamentos assíncronos.
5. **Concorrência e Race Conditions (TOCTOU):** Disparo paralelo de requisições simultâneas para garantir atomicidade de saldo, estoque ou resgate de cupons únicos.
6. **Fronteiras de Segurança:** Rejeição de acesso indevido (IDOR 403), falta de tokens CSRF, mascaramento de PII em logs e payloads genéricos de erro sem vazamento de stack trace.

---

## ⚡ Padrões de Concorrência Poliglotas

Exemplos de implementação de testes de estresse concorrente unitário nas três principais stacks:

### Python (`concurrent.futures.ThreadPoolExecutor`)
```python
from concurrent.futures import ThreadPoolExecutor

def test_should_prevent_double_spend_under_concurrent_race():
    # Arrange
    account = Account(id="acc-1", balance=100)
    service = WithdrawService(account_repo=InMemoryAccountRepo(account))

    # Act: 20 threads paralelas tentando sacar 100 ao mesmo tempo
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(service.withdraw, "acc-1", 100) for _ in range(20)]
        results = [f.result() for f in futures]

    # Assert: Exatamente 1 teve sucesso, 19 falharam
    successes = [r for r in results if r.is_success]
    assert len(successes) == 1
    assert account.balance == 0
```

### TypeScript / Node.js (`Promise.allSettled`)
```typescript
test("should prevent race condition on parallel voucher redemptions", async () => {
    const service = new RedeemVoucherService(new InMemoryVoucherRepo({ code: "OFF50", usageLimit: 1 }));

    // Act: 20 chamadas paralelas
    const attempts = Array.from({ length: 20 }, () => service.execute({ code: "OFF50", userId: "u-1" }));
    const results = await Promise.allSettled(attempts);

    // Assert: Apenas 1 promessa cumprida
    const fulfilled = results.filter(r => r.status === "fulfilled");
    expect(fulfilled.length).toBe(1);
});
```

### Flutter / Dart (`Future.wait`)
```dart
test("should prevent double decrement on concurrent stock reservation", () async {
    final service = ReserveStockUseCase(repository: InMemoryStockRepo(initialStock: 1));

    // Act: 20 chamadas simultâneas
    final attempts = List.generate(20, (_) => service.reserve(productId: "p-1", quantity: 1));
    final results = await Future.wait(
        attempts.map((f) => f.then((_) => true).catchError((_) => false))
    );

    // Assert: Apenas 1 retorna true
    expect(results.where((s) => s).length, equals(1));
});
```

---

## 🔒 Padrões de Teste de Segurança em TDD

1. **IDOR / Controle de Acesso:**
   * Executa o serviço usando o ID do usuário A tentando buscar recurso pertencente ao usuário B.
   * Faz `assert` de que lança `ForbiddenException` (HTTP 403).
2. **Log Capture Fixture (Sem Vazamento de PII):**
   * Usa fixtures de captura de log (`caplog` no pytest).
   * Executa cadastro ou login e valida: `assert "password123" not in caplog.text` e `assert "123.456.789-00" not in caplog.text`.
3. **Payload Seguro de Erro (Fail Securely):**
   * Simula falha catastrófica de banco no mock.
   * Valida que o payload retornado para o cliente é genérico (`{"error": "INTERNAL_ERROR"}`) e que palavras como `Traceback` ou caminhos internos de arquivos não constam no corpo da resposta.

---

## 📋 Arquivos da Skill
* **Instruções Principais:** [`skills/tdd-tests/SKILL.md`](../../skills/implement/SKILL.md)
* **Guia de Padrões AAA & Mocks:** [`skills/tdd-tests/references/aaa_mock_patterns.md`](../../skills/implement/references/tdd-test.md)
