#!/usr/bin/env python3
"""
skills/implement/scripts/pytest_sandbox.py
Pytest Network Isolation Sandbox Plugin [IMP-ASI05-01]

Protects test execution against unintended or malicious external network calls (RCE, SSRF, data exfiltration)
during unit tests by intercepting `socket.socket.connect` and `socket.socket.connect_ex`.

Usage:
  pytest tests/unit/ -v -p skills.implement.scripts.pytest_sandbox

Features:
- Permits local loopback connections (127.0.0.0/8, ::1, localhost, 0.0.0.0, Unix sockets) for internal mocks.
- Explicitly blocks any external IP / hostname with RuntimeError [IMP-ASI05-01].
- Controlled bypass available via @pytest.mark.allow_network on integration tests.
"""

import sys
import ipaddress
import socket
from typing import Any, Tuple, Union

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}

_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex
_is_patched = False


def is_local_address(address: Any) -> bool:
    """
    Checks if a target socket address is a local loopback address or Unix socket.
    Returns True for:
    - Unix domain sockets (str or bytes path)
    - IPv4 loopback (127.0.0.0/8, 0.0.0.0, localhost)
    - IPv6 loopback (::1, localhost)
    Returns False for external IPs, LAN IPs, and domain names.
    """
    if isinstance(address, (str, bytes)):
        # AF_UNIX socket path
        return True

    if isinstance(address, tuple) and len(address) >= 1:
        host = address[0]
        if not isinstance(host, str):
            return False
        host_str = host.strip().lower()
        if host_str in LOOPBACK_HOSTS:
            return True
        try:
            ip = ipaddress.ip_address(host_str)
            return ip.is_loopback
        except ValueError:
            # Domain name or unparseable address -> external
            return False

    return False


def _sandboxed_connect(self, address: Union[Tuple[Any, ...], str, bytes]) -> Any:
    if is_local_address(address):
        return _original_connect(self, address)
    raise RuntimeError(
        f"Security Error [IMP-ASI05-01]: Conexão de rede externa bloqueada em teste unitário ({address}). "
        "Utilize mocks/stubs locais ou a marcação @pytest.mark.allow_network para testes de integração autorizados."
    )


def _sandboxed_connect_ex(self, address: Union[Tuple[Any, ...], str, bytes]) -> Any:
    if is_local_address(address):
        return _original_connect_ex(self, address)
    raise RuntimeError(
        f"Security Error [IMP-ASI05-01]: Conexão de rede externa bloqueada em teste unitário ({address}). "
        "Utilize mocks/stubs locais ou a marcação @pytest.mark.allow_network para testes de integração autorizados."
    )


def enable_sandbox() -> None:
    """Activates the network isolation sandbox by patching socket connect."""
    global _is_patched
    if not _is_patched:
        socket.socket.connect = _sandboxed_connect
        socket.socket.connect_ex = _sandboxed_connect_ex
        _is_patched = True


def disable_sandbox() -> None:
    """Deactivates the network isolation sandbox, restoring original socket connect."""
    global _is_patched
    if _is_patched:
        socket.socket.connect = _original_connect
        socket.socket.connect_ex = _original_connect_ex
        _is_patched = False


def is_sandbox_enabled() -> bool:
    """Returns True if the socket sandbox is currently active."""
    return _is_patched


# ==============================================================================
# Pytest Hooks
# ==============================================================================

def pytest_configure(config: Any) -> None:
    """Registers custom markers for the sandbox plugin."""
    if hasattr(config, "addinivalue_line"):
        config.addinivalue_line(
            "markers",
            "allow_network: allow external network connections in this test (IMP-ASI05-01 sandbox bypass)."
        )


def pytest_runtest_setup(item: Any) -> None:
    """
    Pytest hook executed before each test item.
    Enforces sandbox unless the test item has @pytest.mark.allow_network.
    """
    marker = getattr(item, "get_closest_marker", None)
    if marker and marker("allow_network"):
        disable_sandbox()
    else:
        enable_sandbox()


def pytest_runtest_teardown(item: Any, nextitem: Any = None) -> None:
    """
    Pytest hook executed after each test item.
    Restores clean socket state after test execution.
    """
    disable_sandbox()


if __name__ == "__main__":
    print("pytest_sandbox: Pytest network isolation sandbox plugin [IMP-ASI05-01]")
    sys.exit(0)
