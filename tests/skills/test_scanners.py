#!/usr/bin/env python3
"""
Unit tests for Antigravity review and planning scanner scripts:
- check_arch_boundaries.py
- scan_sinks.py
- ast_complexity.py
- validate_sdd_contracts.py
"""

import sys
import os
import tempfile
import unittest
from pathlib import Path

# Add script locations to sys.path so we can import their modules
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "skills" / "review" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "skills" / "refactor" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "skills" / "plan" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "skills" / "implement" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "skills" / "infra" / "scripts"))

import check_arch_boundaries
import scan_sinks
import ast_complexity
import validate_sdd_contracts
import check_sdd_drift
import audit_dependencies


class TestCheckArchBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_domain_detection_path_segments(self):
        domain_file = self.base_path / "src" / "domain" / "user.py"
        adapter_file = self.base_path / "src" / "adapters" / "domain_service.py"
        test_file = self.base_path / "tests" / "entities_test.py"

        self.assertTrue(check_arch_boundaries.is_domain_file(domain_file))
        # Files merely having 'domain' or 'entities' in filename but not as directory segment should not match
        self.assertFalse(check_arch_boundaries.is_domain_file(adapter_file))
        self.assertFalse(check_arch_boundaries.is_domain_file(test_file))

    def test_commonjs_require_with_parentheses(self):
        domain_dir = self.base_path / "domain"
        domain_dir.mkdir(parents=True, exist_ok=True)
        js_file = domain_dir / "service.js"
        js_file.write_text("const express = require('express');\nconst axios = require('axios');", encoding="utf-8")

        violations, err = check_arch_boundaries.check_file(js_file)
        self.assertIsNone(err)
        self.assertEqual(len(violations), 2)
        self.assertIn("express", violations[0].matched_import)
        self.assertIn("axios", violations[1].matched_import)

    def test_python_domain_leakage(self):
        domain_dir = self.base_path / "entities"
        domain_dir.mkdir(parents=True, exist_ok=True)
        py_file = domain_dir / "model.py"
        py_file.write_text("from sqlalchemy.orm import Session\nimport requests", encoding="utf-8")

        violations, err = check_arch_boundaries.check_file(py_file)
        self.assertIsNone(err)
        self.assertEqual(len(violations), 2)

    def test_dart_flutter_ui_leakage(self):
        domain_dir = self.base_path / "use_cases"
        domain_dir.mkdir(parents=True, exist_ok=True)
        dart_file = domain_dir / "checkout.dart"
        dart_file.write_text("import 'package:flutter/material.dart';\nimport 'dart:io';", encoding="utf-8")

        violations, err = check_arch_boundaries.check_file(dart_file)
        self.assertIsNone(err)
        self.assertEqual(len(violations), 2)

    def test_clean_domain_file_has_no_violations(self):
        domain_dir = self.base_path / "domain"
        domain_dir.mkdir(parents=True, exist_ok=True)
        py_file = domain_dir / "entity.py"
        py_file.write_text("class Order:\n    def __init__(self, id: str):\n        self.id = id\n", encoding="utf-8")

        violations, err = check_arch_boundaries.check_file(py_file)
        self.assertIsNone(err)
        self.assertEqual(len(violations), 0)


class TestScanSinks(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_multiline_command_injection(self):
        py_file = self.base_path / "runner.py"
        py_file.write_text(
            "import subprocess\n"
            "subprocess.Popen(\n"
            "    cmd,\n"
            "    shell=True\n"
            ")\n",
            encoding="utf-8"
        )

        findings, err = scan_sinks.scan_file(py_file)
        self.assertIsNone(err)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule.rule_id, "SEC-CMD-01")
        self.assertEqual(findings[0].line_number, 2)

    def test_secret_redaction_in_snippets(self):
        py_file = self.base_path / "config.py"
        raw_token = "secret_key_1234567890123456"
        py_file.write_text(f'api_key = "{raw_token}"\n', encoding="utf-8")

        findings, err = scan_sinks.scan_file(py_file)
        self.assertIsNone(err)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule.rule_id, "SEC-SECRET-01")
        # Ensure the raw token does NOT appear in snippet
        self.assertNotIn(raw_token, findings[0].snippet)
        self.assertIn("***REDACTED***", findings[0].snippet)

    def test_multiline_cors_detection(self):
        js_file = self.base_path / "server.js"
        js_file.write_text(
            "const corsOptions = {\n"
            "    origin: '*',\n"
            "    credentials: true\n"
            "};\n"
            "app.use(cors(corsOptions));\n",
            encoding="utf-8"
        )

        findings, err = scan_sinks.scan_file(js_file)
        self.assertIsNone(err)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule.rule_id, "SEC-CORS-01")

    def test_clean_file_passes(self):
        py_file = self.base_path / "clean.py"
        py_file.write_text("import secrets\ntoken = secrets.token_hex(16)\n", encoding="utf-8")

        findings, err = scan_sinks.scan_file(py_file)
        self.assertIsNone(err)
        self.assertEqual(len(findings), 0)


class TestAstComplexity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_nested_function_scope_isolation(self):
        """
        An outer function with low complexity must NOT inherit the complexity of an inner helper.
        """
        py_file = self.base_path / "scopes.py"
        code = '''
def outer_simple(val):
    if val > 0:
        x = 1
    else:
        x = 2
    
    def inner_complex(n):
        if n == 1: pass
        elif n == 2: pass
        elif n == 3: pass
        elif n == 4: pass
        elif n == 5: pass
        elif n == 6: pass
        elif n == 7: pass
        elif n == 8: pass
        elif n == 9: pass
        elif n == 10: pass
        elif n == 11: pass
        return n
    
    return inner_complex(x)
'''
        py_file.write_text(code, encoding="utf-8")
        result = ast_complexity.scan_file(py_file, threshold=10)
        self.assertNotIn("error", result)

        high_complex_names = [f["name"] for f in result["high_complexity"]]
        # Only inner_complex should exceed threshold 10!
        # outer_simple has V(G) = 2 (base 1 + 1 'if'), so it must NOT be flagged.
        self.assertIn("inner_complex", high_complex_names)
        self.assertNotIn("outer_simple", high_complex_names)

    def test_asymptotic_heuristics(self):
        py_file = self.base_path / "loops.py"
        code = '''
def check_loops(matrix, targets):
    for row in matrix:
        for val in row:
            if val in targets:
                print(val)
'''
        py_file.write_text(code, encoding="utf-8")
        result = ast_complexity.scan_file(py_file, threshold=10)
        self.assertNotIn("error", result)

        warning_types = [w["type"] for w in result["warnings"]]
        self.assertIn("O(n^2) Nested Loop", warning_types)
        self.assertIn("Linear Search in Loop", warning_types)


class TestValidateSddContracts(unittest.TestCase):
    def _build_sdd_markdown(self, seq_body: str, class_body: str, extra_contracts: str = "DuplicateEntityError") -> str:
        return f"""# SDD Test Specification

## 1. Technical Goal
Test goal

## 2. Sequential Implementation Plan
1. Step one

## 3. Architecture & Contracts

```mermaid
sequenceDiagram
    autonumber
{seq_body}
```

```mermaid
classDiagram
{class_body}
```

### Typed Contracts
Raises `{extra_contracts}` on invalid state.

## 4. File Impact Analysis
| File | Type |
|---|---|
| `a.py` | Additive |
"""

    def test_valid_sdd_with_method_and_bdd_parity_passes(self):
        seq = (
            '    Client->>API: "POST /users (DTO)"\n'
            '    API->>Service: "register_user(dto)"\n'
            '    alt Duplicate Email\n'
            '        Service-->>API: "DuplicateEntityError"\n'
            '    else Valid\n'
            '        Service->>Repo: "save(user)"\n'
            '        Repo-->>Service: "saved_user"\n'
            '    end'
        )
        cls = (
            "    class UserService {\n"
            "        +register_user(dto: DTO) User\n"
            "    }\n"
            "    class IUserRepo {\n"
            "        <<Interface>>\n"
            "        +save(user: User) User\n"
            "    }"
        )
        bdd = """Feature: User Registration
  @happy-path
  Scenario: Valid user
    Given a valid email
  @unhappy-path
  Scenario: Duplicate email
    Given an existing email
"""
        sdd_md = self._build_sdd_markdown(seq, cls)
        self.assertTrue(validate_sdd_contracts.validate_sdd_content(sdd_md, "sdd-test.md", bdd_content=bdd))

    def test_method_parity_mismatch_fails(self):
        seq = (
            '    API->>Service: "register_user(dto)"\n'
            '    Service->>Repo: "find_by_nonexistent_method(key)"'
        )
        cls = (
            "    class UserService {\n"
            "        +register_user(dto: DTO) User\n"
            "    }\n"
            "    class IUserRepo {\n"
            "        +save(user: User) User\n"
            "    }"
        )
        sdd_md = self._build_sdd_markdown(seq, cls)
        self.assertFalse(validate_sdd_contracts.validate_sdd_content(sdd_md, "sdd-mismatch.md"))

    def test_bdd_unhappy_path_missing_alt_branch_fails(self):
        seq = '    API->>Service: "register_user(dto)"'
        cls = (
            "    class UserService {\n"
            "        +register_user(dto: DTO) User\n"
            "    }"
        )
        bdd = """Feature: User Registration
  @unhappy-path
  Scenario: Duplicate email
    Given an existing email
"""
        sdd_md = self._build_sdd_markdown(seq, cls)
        self.assertFalse(validate_sdd_contracts.validate_sdd_content(sdd_md, "sdd-no-alt.md", bdd_content=bdd))


class TestCheckSddDrift(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.sdd_file = self.base_path / "sdd-payment.md"
        self.sdd_file.write_text(
            """# SDD Payment
## 3. Architecture & Contracts
```mermaid
classDiagram
    class IPaymentGateway {
        <<Interface>>
        +charge(user_id: str, amount: Decimal) dict
    }
    class ProcessPaymentUseCase {
        +execute(request: PaymentRequest) PaymentResult
        -_format_result(raw: dict) PaymentResult
    }
    class InMemoryPaymentGateway {
        <<Fake>>
        +charge(user_id: str, amount: Decimal) dict
    }
```

```yaml
contracts:
  - name: "ProcessPayment"
    exceptions:
      - name: "PaymentDeniedError"
        status_code: 402
```

## 4. File Impact Analysis
| File Path | Change Type |
|---|---|
| `src/payment/service.py` | Additive |
""",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_zero_drift_passes_full_gate(self):
        src_dir = self.base_path / "src" / "payment"
        src_dir.mkdir(parents=True, exist_ok=True)
        svc_file = src_dir / "service.py"
        svc_file.write_text(
            "class PaymentDeniedError(Exception): pass\n"
            "class IPaymentGateway:\n"
            "    def charge(self, user_id, amount): pass\n"
            "class ProcessPaymentUseCase:\n"
            "    def execute(self, request): pass\n",
            encoding="utf-8",
        )
        findings, errors = check_sdd_drift.check_drift(
            self.sdd_file, [svc_file], batch_mode=False, check_files=True
        )
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(findings), 0)

    def test_batch_mode_ignores_future_classes_but_catches_missing_method(self):
        src_dir = self.base_path / "src" / "payment"
        src_dir.mkdir(parents=True, exist_ok=True)
        svc_file = src_dir / "service.py"
        # Batch 1 only implements IPaymentGateway, but forgot 'charge' method
        svc_file.write_text(
            "class IPaymentGateway:\n"
            "    def wrong_method_name(self): pass\n",
            encoding="utf-8",
        )
        findings, errors = check_sdd_drift.check_drift(
            self.sdd_file, [svc_file], batch_mode=True
        )
        self.assertEqual(len(errors), 0)
        # Should NOT complain about missing ProcessPaymentUseCase or PaymentDeniedError in batch_mode,
        # but MUST flag missing IPaymentGateway.charge
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "MISSING_METHOD")
        self.assertEqual(findings[0].symbol, "IPaymentGateway.charge")

    def test_pivots_file_authorizes_drift(self):
        src_dir = self.base_path / "src" / "payment"
        src_dir.mkdir(parents=True, exist_ok=True)
        svc_file = src_dir / "service.py"
        svc_file.write_text(
            "class IPaymentGateway:\n"
            "    def charge(self, user_id, amount): pass\n"
            "class ProcessPaymentUseCase:\n"
            "    def execute(self, request): pass\n",
            encoding="utf-8",
        )
        pivots_file = self.base_path / "pivots-payment.md"
        pivots_file.write_text(
            "Replaced PaymentDeniedError with standard HTTPException in controller.",
            encoding="utf-8",
        )
        findings, errors = check_sdd_drift.check_drift(
            self.sdd_file, [svc_file], pivots_path=pivots_file, batch_mode=False
        )
        self.assertEqual(len(errors), 0)
        unauthorized = [f for f in findings if not f.authorized_by_pivot]
        authorized = [f for f in findings if f.authorized_by_pivot]
        self.assertEqual(len(unauthorized), 0)
        self.assertEqual(len(authorized), 1)
        self.assertEqual(authorized[0].symbol, "PaymentDeniedError")


class TestAuditDependencies(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_hallucinated_pypi_package_detected(self):
        def fake_fetcher(url: str):
            return 404, None

        res = audit_dependencies.audit_package("pypi", "hallucinated-ai-magic-sdk", fetcher=fake_fetcher)
        self.assertFalse(res.exists)
        self.assertTrue(any("HALLUCINATION / MISSING" in e for e in res.errors))

    def test_slopsquatting_heuristics_young_package_and_no_repo(self):
        def fake_fetcher(url: str):
            return 200, {
                "info": {
                    "version": "0.1.0",
                    "project_urls": {},
                    "home_page": None,
                },
                "releases": {
                    "0.1.0": [{"upload_time_iso_8601": "2026-10-28T12:00:00Z"}]
                },
            }

        res = audit_dependencies.audit_package("pypi", "suspicious-pkg", fetcher=fake_fetcher, min_age_days=60)
        self.assertTrue(res.exists)
        self.assertTrue(res.needs_web_audit)
        self.assertTrue(any("NEW_PACKAGE" in w for w in res.warnings))
        self.assertTrue(any("NO_REPO" in w for w in res.warnings))
        self.assertTrue(any("SINGLE_RELEASE" in w for w in res.warnings))

    def test_dart_flutter_pub_dev_audit_and_import_parity(self):
        pubspec = self.base_path / "pubspec.yaml"
        pubspec.write_text(
            "name: my_flutter_app\n"
            "dependencies:\n"
            "  flutter:\n"
            "    sdk: flutter\n"
            "  provider: ^6.1.0\n",
            encoding="utf-8",
        )
        lib_dir = self.base_path / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)
        dart_file = lib_dir / "main.dart"
        dart_file.write_text(
            "import 'package:flutter/material.dart';\n"
            "import 'package:provider/provider.dart';\n"
            "import 'package:hallucinated_flutter_pkg/widget.dart';\n",
            encoding="utf-8",
        )

        eco, deps, local_names = audit_dependencies.parse_manifest(pubspec)
        self.assertEqual(eco, "pub")
        self.assertIn("provider", deps)
        self.assertNotIn("flutter", deps)

        errors = audit_dependencies.verify_import_parity(lib_dir, eco, deps, local_names)
        self.assertEqual(len(errors), 1)
        self.assertIn("hallucinated_flutter_pkg", errors[0])

    def test_python_ast_import_parity_maps_known_aliases(self):
        pyproject = self.base_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "demo"\ndependencies = ["beautifulsoup4>=4.12.0", "pyyaml==6.0.1"]\n',
            encoding="utf-8",
        )
        src_dir = self.base_path / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        py_file = src_dir / "app.py"
        py_file.write_text(
            "import os\n"
            "import yaml\n"
            "from bs4 import BeautifulSoup\n"
            "import non_existent_ghost_lib\n",
            encoding="utf-8",
        )

        eco, deps, local_names = audit_dependencies.parse_manifest(pyproject)
        errors = audit_dependencies.verify_import_parity(src_dir, eco, deps, local_names)
        self.assertEqual(len(errors), 1)
        self.assertIn("non_existent_ghost_lib", errors[0])


if __name__ == "__main__":
    unittest.main()
