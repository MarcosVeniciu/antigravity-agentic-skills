#!/usr/bin/env python3
"""
skills/infra/scripts/audit_dependencies.py
Multi-ecosystem Dependency Existence, Anti-Slopsquatting & Import Parity Auditor.

Enforces:
1. Package existence and version verification across public registries:
   - Python (PyPI: pyproject.toml, requirements.txt)
   - Node/TypeScript (npm: package.json)
   - Dart/Flutter (pub.dev: pubspec.yaml)
   - Rust (crates.io: Cargo.toml)
   - Go (proxy.golang.org: go.mod)
   - .NET/C# (NuGet: *.csproj)
   - PHP (Packagist: composer.json)
2. Anti-Slopsquatting & Typosquatting heuristics:
   - Flags recently created packages (< 60 days old).
   - Flags packages missing verifiable source repository URLs.
   - Flags repository URL spoofing / slug mismatch ([SLOPSQUATTING_RISK: REPO_MISMATCH]).
   - Flags deprecated, yanked, or discontinued packages.
   - Flags scarce release history (< 2 releases when newly published).
3. Anti-SSRF & Registry Allowlisting ([INF-ASI02-04]):
   - Enforces HTTPS-only connections to official registries and blocks private/loopback/link-local redirects.
4. Source Import Parity (--scan-imports):
   - Scans source trees (Python AST + dynamic imports, Node ES/CJS/dynamic imports, Dart 'package:' imports)
     and cross-references imported packages against declared manifest dependencies.
5. Subagent Escalation Signal ([NEEDS_WEB_AUDIT]):
   - Emits structured escalation triggers for the `dependency-auditor` subagent
     when encountering unknown ecosystems, suspicious slopsquatting signals, or unmapped imports.
"""

import argparse
import ast
import ipaddress
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

# Fix Windows cp1252 console crash when printing unicode symbols
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_HOSTS = ("github.com", "gitlab.com", "bitbucket.org", "codeberg.org", "golang.org")

ALLOWED_REGISTRY_HOSTS: Set[str] = {
    "pypi.org",
    "registry.npmjs.org",
    "pub.dev",
    "crates.io",
    "proxy.golang.org",
    "api.nuget.org",
    "repo.packagist.org",
    "api.osv.dev",
}

PYTHON_IMPORT_TO_PYPI: Dict[str, str] = {
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "fitz": "pymupdf",
    "gi": "pygobject",
    "google": "protobuf",
    "jose": "python-jose",
    "jwt": "pyjwt",
    "magic": "python-magic",
    "multipart": "python-multipart",
    "openai": "openai",
    "pil": "pillow",
    "pillow": "pillow",
    "psycopg2": "psycopg2-binary",
    "rest_framework": "djangorestframework",
    "serial": "pyserial",
    "skimage": "scikit-image",
    "sklearn": "scikit-learn",
    "typing_extensions": "typing-extensions",
    "usb": "pyusb",
    "win32api": "pywin32",
    "win32com": "pywin32",
    "wx": "wxpython",
    "yaml": "pyyaml",
    "zmq": "pyzmq",
}

PYTHON_STDLIB_EXTRAS: Set[str] = {
    "__future__", "_thread", "abc", "argparse", "array", "ast", "asyncio", "atexit",
    "base64", "bdb", "binascii", "bisect", "builtins", "bz2", "calendar", "cmath",
    "cmd", "code", "codecs", "codeop", "collections", "colorsys", "compileall",
    "concurrent", "configparser", "contextlib", "contextvars", "copy", "copyreg",
    "cProfile", "csv", "ctypes", "curses", "dataclasses", "datetime", "dbm",
    "decimal", "difflib", "dis", "doctest", "email", "encodings", "enum", "errno",
    "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch", "fractions",
    "ftplib", "functools", "gc", "getopt", "getpass", "gettext", "glob", "graphlib",
    "grp", "gzip", "hashlib", "heapq", "hmac", "html", "http", "imaplib",
    "importlib", "inspect", "io", "ipaddress", "itertools", "json", "keyword",
    "linecache", "locale", "logging", "lzma", "mailbox", "marshal", "math",
    "mimetypes", "mmap", "modulefinder", "msvcrt", "multiprocessing", "netrc",
    "numbers", "operator", "optparse", "os", "pathlib", "pdb", "pickle",
    "pickletools", "pkgutil", "platform", "plistlib", "poplib", "posix", "pprint",
    "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr", "pydoc", "queue",
    "quopri", "random", "re", "readline", "reprlib", "resource", "rlcompleter",
    "runpy", "sched", "secrets", "select", "selectors", "shelve", "shlex", "shutil",
    "signal", "site", "smtplib", "socket", "socketserver", "sqlite3", "ssl", "stat",
    "statistics", "string", "stringprep", "struct", "subprocess", "symtable", "sys",
    "sysconfig", "syslog", "tabnanny", "tarfile", "tempfile", "termios", "test",
    "textwrap", "threading", "time", "timeit", "tkinter", "token", "tokenize",
    "tomllib", "trace", "traceback", "tracemalloc", "tty", "turtle", "types",
    "typing", "unicodedata", "unittest", "urllib", "uuid", "venv", "warnings",
    "wave", "weakref", "webbrowser", "winreg", "winsound", "wsgiref", "xdrlib",
    "xml", "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib", "zoneinfo",
}

NODE_BUILTINS: Set[str] = {
    "assert", "async_hooks", "buffer", "child_process", "cluster", "console",
    "constants", "crypto", "dgram", "diagnostics_channel", "dns", "domain",
    "events", "fs", "http", "http2", "https", "inspector", "module", "net", "os",
    "path", "perf_hooks", "process", "punycode", "querystring", "readline", "repl",
    "stream", "string_decoder", "sys", "test", "timers", "tls", "trace_events",
    "tty", "url", "util", "v8", "vm", "wasi", "worker_threads", "zlib",
}

DART_SDK_PACKAGES: Set[str] = {
    "flutter", "flutter_test", "flutter_driver", "flutter_localizations",
    "flutter_web_plugins", "integration_test",
}

EXCLUDED_DIRS: Set[str] = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".dart_tool", "build", "dist", "target", ".pytest_cache",
}


@dataclass
class PackageAuditResult:
    ecosystem: str
    name: str
    requested_version: Optional[str] = None
    exists: bool = False
    latest_version: Optional[str] = None
    version_exists: bool = True
    deprecated: bool = False
    repository_url: Optional[str] = None
    age_days: Optional[int] = None
    release_count: int = 0
    needs_web_audit: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# -----------------------------------------------------------------------------
# Shared Helpers & Anti-SSRF Gate
# -----------------------------------------------------------------------------
def _is_forbidden_host_or_ip(host: str) -> bool:
    if not host or host in ("localhost", "localhost.localdomain"):
        return True
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
        return (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


def is_allowed_registry_url(url: str) -> bool:
    """
    Validates that a URL uses HTTPS, does not target loopback/private/link-local IPs,
    and belongs strictly to the official package registry allowlist ([INF-ASI02-04]).
    """
    if not isinstance(url, str) or not url.strip():
        return False
    try:
        parsed = urllib.parse.urlparse(url.strip())
    except ValueError:
        return False
    if parsed.scheme.lower() != "https":
        return False
    host = (parsed.hostname or "").lower().rstrip(".")
    if _is_forbidden_host_or_ip(host):
        return False
    return host in ALLOWED_REGISTRY_HOSTS


class SafeRegistryRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Blocks redirects to non-HTTPS URLs, private/loopback IPs, or unapproved hosts."""

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        resolved_url = urllib.parse.urljoin(req.full_url, newurl)
        if not is_allowed_registry_url(resolved_url):
            raise urllib.error.URLError(f"SSRF Protection: Blocked redirect to untrusted URL '{resolved_url}'")
        return super().redirect_request(req, fp, code, msg, headers, resolved_url)


def normalize_pkg_name(name: str, ecosystem: str) -> str:
    cleaned = name.strip()
    if ecosystem in ("pypi", "python"):
        return re.sub(r"[-_.]+", "-", cleaned).lower()
    return cleaned.lower()


def parse_iso_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str or not isinstance(date_str, str):
        return None
    cleaned = date_str.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(cleaned)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return _parse_fallback_date(date_str)


def _parse_fallback_date(date_str: str) -> Optional[datetime]:
    m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", date_str)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def compute_age_days(dates: Iterable[Optional[str]]) -> Optional[int]:
    parsed = [dt for d in dates if (dt := parse_iso_date(d)) is not None]
    if not parsed:
        return None
    earliest = min(parsed)
    return max(0, (datetime.now(timezone.utc) - earliest).days)


def is_valid_repo_url(url: Any) -> bool:
    if not isinstance(url, str) or not url.strip():
        return False
    lower = url.lower()
    return any(lower.find(h) != -1 for h in REPO_HOSTS)


def first_valid_repo(candidates: Iterable[Any]) -> Optional[str]:
    for cand in candidates:
        if is_valid_repo_url(cand):
            return str(cand).strip()
    return None


def clean_exact_version(version_spec: Optional[str]) -> Optional[str]:
    if not version_spec:
        return None
    spec = version_spec.strip()
    m = re.match(
        r"^(?:==|\^|~|>=|<=|=)?\s*([0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)$",
        spec,
    )
    return m.group(1) if m else None


def default_http_fetcher(url: str, timeout: float = 8.0) -> Tuple[int, Optional[Any]]:
    if not is_allowed_registry_url(url):
        return 0, f"SSRF Protection: Blocked request to untrusted registry URL '{url}'"

    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Antigravity-Infra-Dependency-Auditor/1.0",
        },
    )
    opener = urllib.request.build_opener(SafeRegistryRedirectHandler())
    try:
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), _safe_json_loads(raw)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return 0, str(e)


def _safe_json_loads(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _handle_http_status(res: PackageAuditResult, status: int, data: Any, registry_label: str) -> bool:
    """Returns True if valid 200 JSON dict received; populates errors/warnings otherwise."""
    if status in (404, 410):
        res.exists = False
        res.errors.append(
            f"[HALLUCINATION / MISSING] Package '{res.name}' does NOT exist on {registry_label} (HTTP {status})."
        )
        return False
    if status != 200 or not isinstance(data, dict):
        res.needs_web_audit = True
        res.warnings.append(
            f"[NEEDS_WEB_AUDIT] Could not verify '{res.name}' on {registry_label} (status={status})."
        )
        return False
    res.exists = True
    return True


def _check_version_membership(
    res: PackageAuditResult, available_versions: Set[str], registry_label: str
) -> Optional[str]:
    clean_ver = clean_exact_version(res.requested_version)
    if clean_ver and clean_ver not in available_versions:
        res.version_exists = False
        res.errors.append(
            f"[INVALID_VERSION] Version '{clean_ver}' of '{res.name}' does NOT exist on {registry_label}. "
            f"Latest stable is '{res.latest_version}'."
        )
    return clean_ver


def _does_repo_match_package(pkg_name: str, repo_url: str) -> bool:
    """
    Checks whether the normalized package name (stripping scopes, prefixes, and punctuation)
    correlates with the repository URL path/slug ([INF-ASI04-03]).
    """
    raw = pkg_name.strip().lower()
    if raw.startswith("@") and "/" in raw:
        raw = raw.split("/", 1)[1]
    elif "/" in raw:
        raw = raw.split("/")[-1]

    candidates = {re.sub(r"[-_.]+", "", raw)}
    for prefix in ("python-", "py-", "py", "dart-", "flutter-", "flutter_", "rust-", "go-", "node-"):
        if raw.startswith(prefix) and len(raw) > len(prefix) + 1:
            candidates.add(re.sub(r"[-_.]+", "", raw[len(prefix) :]))
    for suffix in ("-py", "-python", "-js", "-dart", "-rs"):
        if raw.endswith(suffix) and len(raw) > len(suffix) + 1:
            candidates.add(re.sub(r"[-_.]+", "", raw[: -len(suffix)]))

    cleaned_repo = re.sub(r"\.git$", "", repo_url.strip().lower())
    norm_repo = re.sub(r"[-_.]+", "", cleaned_repo)
    return any(c and c in norm_repo for c in candidates)


def apply_slopsquatting_heuristics(res: PackageAuditResult, min_age_days: int = 60) -> None:
    if not res.exists:
        return
    if res.age_days is not None and res.age_days < min_age_days:
        res.needs_web_audit = True
        res.warnings.append(
            f"[SLOPSQUATTING_RISK: NEW_PACKAGE] '{res.name}' ({res.ecosystem}) was first published "
            f"only {res.age_days} day(s) ago (< {min_age_days}d). Requires `dependency-auditor` web verification."
        )
    if not res.repository_url:
        res.needs_web_audit = True
        res.warnings.append(
            f"[SLOPSQUATTING_RISK: NO_REPO] '{res.name}' ({res.ecosystem}) has no verifiable source repository "
            "linked in registry metadata. Requires `dependency-auditor` web verification."
        )
    elif not _does_repo_match_package(res.name, res.repository_url):
        res.needs_web_audit = True
        res.warnings.append(
            f"[SLOPSQUATTING_RISK: REPO_MISMATCH] Repository URL slug does not match package name "
            f"('{res.name}' vs '{res.repository_url}'). Requires `dependency-auditor` web verification."
        )
    if res.release_count <= 1 and (res.age_days is None or res.age_days < 180):
        res.needs_web_audit = True
        res.warnings.append(
            f"[SLOPSQUATTING_RISK: SINGLE_RELEASE] '{res.name}' ({res.ecosystem}) has only "
            f"{res.release_count} release(s). Verify authenticity via `dependency-auditor`."
        )


# -----------------------------------------------------------------------------
# Registry Auditors (V(G) <= 10 per function)
# -----------------------------------------------------------------------------
def audit_pypi_package(
    name: str,
    requested_version: Optional[str],
    fetcher: Callable[[str], Tuple[int, Any]],
    min_age_days: int = 60,
) -> PackageAuditResult:
    res = PackageAuditResult(ecosystem="pypi", name=name, requested_version=requested_version)
    status, data = fetcher(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json")
    if not _handle_http_status(res, status, data, "PyPI"):
        return res

    info = data.get("info") or {}
    releases = data.get("releases") or {}
    res.latest_version = info.get("version")
    res.release_count = len(releases)

    clean_ver = _check_version_membership(res, set(releases.keys()), "PyPI")
    _check_pypi_deprecation(res, info, releases, clean_ver)
    res.repository_url = _extract_pypi_repo(info)
    res.age_days = _extract_pypi_age_days(releases)
    apply_slopsquatting_heuristics(res, min_age_days=min_age_days)
    return res


def _check_pypi_deprecation(
    res: PackageAuditResult, info: Dict[str, Any], releases: Dict[str, Any], clean_ver: Optional[str]
) -> None:
    files = releases.get(clean_ver or "", [])
    if files and all(isinstance(f, dict) and f.get("yanked") for f in files):
        res.deprecated = True
        res.warnings.append(f"[YANKED] Version '{clean_ver}' of '{res.name}' is yanked on PyPI.")
    classifiers = " ".join(str(c) for c in (info.get("classifiers") or []))
    if "Inactive" in classifiers or "Deprecated" in classifiers:
        res.deprecated = True
        res.warnings.append(f"[DEPRECATED] Package '{res.name}' is marked Inactive/Deprecated on PyPI.")


def _extract_pypi_repo(info: Dict[str, Any]) -> Optional[str]:
    proj_urls = info.get("project_urls") or {}
    candidates = list(proj_urls.values()) if isinstance(proj_urls, dict) else []
    candidates.extend([info.get("home_page"), info.get("package_url")])
    return first_valid_repo(candidates)


def _extract_pypi_age_days(releases: Dict[str, Any]) -> Optional[int]:
    upload_dates: List[Optional[str]] = []
    for ver_files in releases.values():
        if isinstance(ver_files, list) and ver_files and isinstance(ver_files[0], dict):
            upload_dates.append(ver_files[0].get("upload_time_iso_8601") or ver_files[0].get("upload_time"))
    return compute_age_days(upload_dates)


def audit_npm_package(
    name: str,
    requested_version: Optional[str],
    fetcher: Callable[[str], Tuple[int, Any]],
    min_age_days: int = 60,
) -> PackageAuditResult:
    res = PackageAuditResult(ecosystem="npm", name=name, requested_version=requested_version)
    status, data = fetcher(f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='@/')}")
    if not _handle_http_status(res, status, data, "npm"):
        return res

    versions = data.get("versions") or {}
    res.latest_version = (data.get("dist-tags") or {}).get("latest")
    res.release_count = len(versions)

    clean_ver = _check_version_membership(res, set(versions.keys()), "npm")
    target_meta = versions.get(clean_ver or res.latest_version or "") or {}
    _populate_npm_metadata(res, data, target_meta)
    apply_slopsquatting_heuristics(res, min_age_days=min_age_days)
    return res


def _populate_npm_metadata(res: PackageAuditResult, data: Dict[str, Any], target_meta: Dict[str, Any]) -> None:
    dep_msg = target_meta.get("deprecated") or data.get("deprecated")
    if dep_msg:
        res.deprecated = True
        res.warnings.append(f"[DEPRECATED] npm package '{res.name}' is deprecated: {dep_msg}")

    repo = data.get("repository") or target_meta.get("repository")
    repo_url = repo.get("url") if isinstance(repo, dict) else repo
    res.repository_url = first_valid_repo([repo_url, data.get("homepage"), target_meta.get("homepage")])
    res.age_days = compute_age_days([(data.get("time") or {}).get("created")])


def audit_pub_package(
    name: str,
    requested_version: Optional[str],
    fetcher: Callable[[str], Tuple[int, Any]],
    min_age_days: int = 60,
) -> PackageAuditResult:
    res = PackageAuditResult(ecosystem="pub", name=name, requested_version=requested_version)
    status, data = fetcher(f"https://pub.dev/api/packages/{urllib.parse.quote(name)}")
    if not _handle_http_status(res, status, data, "pub.dev"):
        return res

    latest = data.get("latest") or {}
    versions = [v for v in (data.get("versions") or []) if isinstance(v, dict)]
    res.latest_version = latest.get("version")
    res.release_count = len(versions)

    _check_version_membership(res, {str(v.get("version")) for v in versions if v.get("version")}, "pub.dev")
    _populate_pub_metadata(res, data, latest, versions)
    apply_slopsquatting_heuristics(res, min_age_days=min_age_days)
    return res


def _populate_pub_metadata(
    res: PackageAuditResult, data: Dict[str, Any], latest: Dict[str, Any], versions: List[Dict[str, Any]]
) -> None:
    if data.get("isDiscontinued"):
        res.deprecated = True
        res.warnings.append(f"[DISCONTINUED] pub.dev package '{res.name}' is discontinued.")
    pubspec = latest.get("pubspec") or {}
    res.repository_url = first_valid_repo(
        [pubspec.get("repository"), pubspec.get("homepage"), pubspec.get("issue_tracker")]
    )
    res.age_days = compute_age_days(v.get("published") for v in versions)


def audit_crates_package(
    name: str,
    requested_version: Optional[str],
    fetcher: Callable[[str], Tuple[int, Any]],
    min_age_days: int = 60,
) -> PackageAuditResult:
    res = PackageAuditResult(ecosystem="crates", name=name, requested_version=requested_version)
    status, data = fetcher(f"https://crates.io/api/v1/crates/{urllib.parse.quote(name)}")
    if not _handle_http_status(res, status, data, "crates.io"):
        return res

    _populate_crates_metadata(res, data)
    apply_slopsquatting_heuristics(res, min_age_days=min_age_days)
    return res


def _populate_crates_metadata(res: PackageAuditResult, data: Dict[str, Any]) -> None:
    crate = data.get("crate") if isinstance(data.get("crate"), dict) else {}
    raw_vers = data.get("versions") if isinstance(data.get("versions"), list) else []
    versions = [v for v in raw_vers if isinstance(v, dict)]
    res.latest_version = crate.get("max_stable_version") or crate.get("max_version")
    res.release_count = len(versions)
    res.repository_url = first_valid_repo([crate.get("repository"), crate.get("homepage")])
    res.age_days = compute_age_days([crate.get("created_at")])
    _check_crates_version_status(res, versions)


def _check_crates_version_status(res: PackageAuditResult, versions: List[Dict[str, Any]]) -> None:
    ver_map = {str(v["num"]): v for v in versions if v.get("num")}
    clean_ver = _check_version_membership(res, set(ver_map.keys()), "crates.io")
    if clean_ver and ver_map.get(clean_ver, {}).get("yanked"):
        res.deprecated = True
        res.warnings.append(f"[YANKED] Crate '{res.name}' version '{clean_ver}' is yanked on crates.io.")


def audit_go_package(
    name: str,
    requested_version: Optional[str],
    fetcher: Callable[[str], Tuple[int, Any]],
    min_age_days: int = 60,
) -> PackageAuditResult:
    res = PackageAuditResult(ecosystem="go", name=name, requested_version=requested_version)
    encoded_mod = re.sub(r"([A-Z])", lambda m: "!" + m.group(1).lower(), name)
    status, data = fetcher(f"https://proxy.golang.org/{encoded_mod}/@latest")
    if not _handle_http_status(res, status, data, "proxy.golang.org"):
        return res

    res.latest_version = data.get("Version")
    res.release_count = 2
    res.repository_url = first_valid_repo([f"https://{name}"])
    _verify_go_requested_version(res, encoded_mod, fetcher)
    return res


def _verify_go_requested_version(
    res: PackageAuditResult, encoded_mod: str, fetcher: Callable[[str], Tuple[int, Any]]
) -> None:
    if not res.requested_version:
        return
    clean_ver = res.requested_version.strip()
    if not clean_ver.startswith("v"):
        clean_ver = "v" + clean_ver
    v_status, _ = fetcher(f"https://proxy.golang.org/{encoded_mod}/@v/{clean_ver}.info")
    if v_status in (404, 410):
        res.version_exists = False
        res.errors.append(
            f"[INVALID_VERSION] Version '{clean_ver}' of Go module '{res.name}' does NOT exist. "
            f"Latest is '{res.latest_version}'."
        )


def audit_nuget_package(
    name: str,
    requested_version: Optional[str],
    fetcher: Callable[[str], Tuple[int, Any]],
    min_age_days: int = 60,
) -> PackageAuditResult:
    res = PackageAuditResult(ecosystem="nuget", name=name, requested_version=requested_version)
    url = f"https://api.nuget.org/v3-flatcontainer/{urllib.parse.quote(name.lower())}/index.json"
    status, data = fetcher(url)
    if not _handle_http_status(res, status, data, "NuGet"):
        return res

    _populate_nuget_metadata(res, data)
    return res


def _populate_nuget_metadata(res: PackageAuditResult, data: Dict[str, Any]) -> None:
    raw_vers = data.get("versions") if isinstance(data.get("versions"), list) else []
    versions = [str(v) for v in raw_vers]
    res.release_count = len(versions)
    stable = [v for v in versions if not v.__contains__("-")]
    res.latest_version = stable[-1] if stable else (versions[-1] if versions else None)
    _check_nuget_version_and_count(res, versions)


def _check_nuget_version_and_count(res: PackageAuditResult, versions: List[str]) -> None:
    clean_ver = clean_exact_version(res.requested_version)
    if clean_ver and clean_ver.lower() not in {v.lower() for v in versions}:
        res.version_exists = False
        res.errors.append(f"[INVALID_VERSION] Version '{clean_ver}' of '{res.name}' not found on NuGet.")
    if res.release_count <= 1:
        res.needs_web_audit = True
        res.warnings.append(f"[SUSPICIOUS_SINGLE_RELEASE] NuGet package '{res.name}' has <= 1 release.")


def audit_packagist_package(
    name: str,
    requested_version: Optional[str],
    fetcher: Callable[[str], Tuple[int, Any]],
    min_age_days: int = 60,
) -> PackageAuditResult:
    res = PackageAuditResult(ecosystem="packagist", name=name, requested_version=requested_version)
    if "/" not in name:
        res.errors.append(f"[INVALID_PACKAGE_NAME] Composer package '{name}' must be 'vendor/package'.")
        return res

    url = f"https://repo.packagist.org/p2/{urllib.parse.quote(name.lower(), safe='/')}.json"
    status, data = fetcher(url)
    if not _handle_http_status(res, status, data, "Packagist"):
        return res

    pkgs = [p for p in ((data.get("packages") or {}).get(name.lower()) or []) if isinstance(p, dict)]
    if not pkgs:
        res.exists = False
        res.errors.append(f"[HALLUCINATION / MISSING] Composer package '{name}' has no releases.")
        return res

    _populate_packagist_metadata(res, pkgs)
    apply_slopsquatting_heuristics(res, min_age_days=min_age_days)
    return res


def _populate_packagist_metadata(res: PackageAuditResult, pkgs: List[Dict[str, Any]]) -> None:
    res.release_count = len(pkgs)
    latest_obj = pkgs[0]
    res.latest_version = latest_obj.get("version")
    source_url = (latest_obj.get("source") or {}).get("url")
    res.repository_url = first_valid_repo([source_url, latest_obj.get("homepage")])
    if latest_obj.get("abandoned"):
        res.deprecated = True
        res.warnings.append(f"[ABANDONED] Composer package '{res.name}' is marked abandoned.")
    res.age_days = compute_age_days(p.get("time") for p in pkgs)


def audit_package(
    ecosystem: str,
    name: str,
    requested_version: Optional[str] = None,
    fetcher: Callable[[str], Tuple[int, Any]] = default_http_fetcher,
    min_age_days: int = 60,
) -> PackageAuditResult:
    eco = ecosystem.lower().strip()
    dispatch = {
        "pypi": audit_pypi_package,
        "python": audit_pypi_package,
        "npm": audit_npm_package,
        "node": audit_npm_package,
        "pub": audit_pub_package,
        "dart": audit_pub_package,
        "flutter": audit_pub_package,
        "crates": audit_crates_package,
        "rust": audit_crates_package,
        "go": audit_go_package,
        "golang": audit_go_package,
        "nuget": audit_nuget_package,
        "dotnet": audit_nuget_package,
        "packagist": audit_packagist_package,
        "php": audit_packagist_package,
    }
    handler = dispatch.get(eco)
    if not handler:
        res = PackageAuditResult(ecosystem=eco, name=name, requested_version=requested_version, needs_web_audit=True)
        res.warnings.append(
            f"[NEEDS_WEB_AUDIT] Ecosystem '{eco}' for '{name}' requires web audit via `dependency-auditor`."
        )
        return res
    return handler(name, requested_version, fetcher, min_age_days=min_age_days)


# -----------------------------------------------------------------------------
# Manifest Parsers (V(G) <= 10 per function)
# -----------------------------------------------------------------------------
def parse_manifest(manifest_path: Path) -> Tuple[str, Dict[str, str], Set[str]]:
    fname = manifest_path.name.lower()
    content = manifest_path.read_text(encoding="utf-8", errors="replace")

    parsers: Dict[str, Callable[[str], Tuple[str, Dict[str, str], Set[str]]]] = {
        "package.json": _parse_package_json,
        "pyproject.toml": _parse_pyproject_toml,
        "pubspec.yaml": _parse_pubspec_yaml,
        "cargo.toml": _parse_cargo_toml,
        "go.mod": _parse_go_mod,
        "composer.json": _parse_composer_json,
    }
    if fname in parsers:
        return parsers[fname](content)
    if fname.startswith("requirements") and fname.endswith(".txt"):
        return _parse_requirements_txt(content)
    if fname.endswith(".csproj"):
        return _parse_csproj(content)
    return ("unknown", {}, set())


def _parse_package_json(content: str) -> Tuple[str, Dict[str, str], Set[str]]:
    data = _safe_json_loads(content)
    if not isinstance(data, dict):
        return ("npm", {}, set())
    local_names = {data["name"]} if isinstance(data.get("name"), str) else set()
    deps: Dict[str, str] = {}
    for sec in ("dependencies", "devDependencies", "peerDependencies"):
        _collect_npm_section(data.get(sec), deps)
    return ("npm", deps, local_names)


def _collect_npm_section(sec_data: Any, deps: Dict[str, str]) -> None:
    if not isinstance(sec_data, dict):
        return
    for k, v in sec_data.items():
        if isinstance(v, str) and not v.startswith(("workspace:", "file:", "link:")):
            deps[k] = v


def _parse_pyproject_toml(content: str) -> Tuple[str, Dict[str, str], Set[str]]:
    try:
        import tomllib
        data = tomllib.loads(content)
    except Exception:
        return ("pypi", {}, set())

    deps: Dict[str, str] = {}
    local_names: Set[str] = set()
    _extract_pep621_deps(data.get("project") or {}, deps, local_names)
    _extract_poetry_deps(((data.get("tool") or {}).get("poetry")) or {}, deps, local_names)
    return ("pypi", deps, local_names)


def _extract_pep621_deps(proj: Dict[str, Any], deps: Dict[str, str], local_names: Set[str]) -> None:
    if isinstance(proj.get("name"), str):
        local_names.add(proj["name"])
    _add_pep508_list(proj.get("dependencies") or [], deps)
    for group_reqs in (proj.get("optional-dependencies") or {}).values():
        _add_pep508_list(group_reqs or [], deps)


def _add_pep508_list(req_list: Iterable[str], deps: Dict[str, str]) -> None:
    for req in req_list:
        pkg, ver = _split_pep508_req(req)
        if pkg:
            deps[pkg] = ver


def _extract_poetry_deps(poetry: Dict[str, Any], deps: Dict[str, str], local_names: Set[str]) -> None:
    if isinstance(poetry.get("name"), str):
        local_names.add(poetry["name"])
    _collect_toml_dep_table(poetry.get("dependencies"), deps)
    _collect_toml_dep_table(poetry.get("dev-dependencies"), deps)
    for grp in (poetry.get("group") or {}).values():
        if isinstance(grp, dict):
            _collect_toml_dep_table(grp.get("dependencies"), deps)


def _collect_toml_dep_table(table: Any, deps: Dict[str, str]) -> None:
    if not isinstance(table, dict):
        return
    for k, v in table.items():
        if k.lower() == "python":
            continue
        ver = _extract_toml_version(v)
        if ver is not None:
            deps[k] = ver


def _extract_toml_version(v: Any) -> Optional[str]:
    if isinstance(v, str):
        return v
    if isinstance(v, dict) and not ("path" in v or "git" in v or "sdk" in v):
        return str(v.get("version", "*"))
    return None


def _split_pep508_req(req_str: str) -> Tuple[Optional[str], str]:
    cleaned = req_str.split(";")[0].strip()
    if not cleaned or cleaned.startswith(("#", "-")) or "://" in cleaned:
        return None, ""
    m = re.match(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]*\])?\s*(.*)$", cleaned)
    return (m.group(1), m.group(2).strip()) if m else (None, "")


def _parse_requirements_txt(content: str) -> Tuple[str, Dict[str, str], Set[str]]:
    deps: Dict[str, str] = {}
    _add_pep508_list((line.split("#")[0].strip() for line in content.splitlines()), deps)
    return ("pypi", deps, set())


def _parse_pubspec_yaml(content: str) -> Tuple[str, Dict[str, str], Set[str]]:
    """Parses Dart/Flutter pubspec.yaml via PyYAML when available, or indentation fallback."""
    parsed = _try_yaml_load(content)
    if isinstance(parsed, dict):
        return _extract_pubspec_from_dict(parsed)
    return _parse_pubspec_fallback(content)


def _try_yaml_load(content: str) -> Any:
    try:
        import yaml  # type: ignore
        return yaml.safe_load(content)
    except Exception:
        return None


def _extract_pubspec_from_dict(data: Dict[str, Any]) -> Tuple[str, Dict[str, str], Set[str]]:
    local_names = {data["name"]} if isinstance(data.get("name"), str) else set()
    deps: Dict[str, str] = {}
    for sec in ("dependencies", "dev_dependencies"):
        _collect_pubspec_section(data.get(sec), deps)
    return ("pub", deps, local_names)


def _collect_pubspec_section(sec_dict: Any, deps: Dict[str, str]) -> None:
    if not isinstance(sec_dict, dict):
        return
    for k, v in sec_dict.items():
        if k in DART_SDK_PACKAGES:
            continue
        if isinstance(v, dict) and ("sdk" in v or "path" in v or "git" in v):
            continue
        deps[k] = str(v) if v is not None else "any"


def _parse_pubspec_fallback(content: str) -> Tuple[str, Dict[str, str], Set[str]]:
    deps: Dict[str, str] = {}
    local_names: Set[str] = set()
    section: Optional[str] = None
    last_pkg: Optional[str] = None

    for raw_line in content.splitlines():
        line = raw_line.split("#")[0].rstrip()
        if not line.strip():
            continue
        section, last_pkg = _process_pubspec_line(line, section, last_pkg, deps, local_names)
    return ("pub", deps, local_names)


def _process_pubspec_line(
    line: str,
    section: Optional[str],
    last_pkg: Optional[str],
    deps: Dict[str, str],
    local_names: Set[str],
) -> Tuple[Optional[str], Optional[str]]:
    indent = len(line) - len(line.lstrip(" "))
    stripped = line.strip()
    if indent == 0:
        return _handle_pubspec_root_line(stripped, local_names), None
    if section and indent == 2 and ":" in stripped:
        return section, _handle_pubspec_dep_line(stripped, deps)
    if section and indent >= 4 and last_pkg and stripped.startswith(("sdk:", "path:", "git:")):
        deps.pop(last_pkg, None)
    return section, last_pkg


def _handle_pubspec_root_line(stripped: str, local_names: Set[str]) -> Optional[str]:
    if stripped.startswith("name:"):
        local_names.add(stripped.split(":", 1)[1].strip().strip("\"'"))
    return stripped[:-1] if stripped in ("dependencies:", "dev_dependencies:") else None


def _handle_pubspec_dep_line(stripped: str, deps: Dict[str, str]) -> str:
    k, v = [p.strip().strip("\"'") for p in stripped.split(":", 1)]
    if k not in DART_SDK_PACKAGES:
        deps[k] = v or "any"
    return k


def _parse_cargo_toml(content: str) -> Tuple[str, Dict[str, str], Set[str]]:
    try:
        import tomllib
        data = tomllib.loads(content)
    except Exception:
        return ("crates", {}, set())

    pkg_name = (data.get("package") or {}).get("name")
    local_names = {pkg_name} if isinstance(pkg_name, str) else set()
    deps: Dict[str, str] = {}
    for sec in ("dependencies", "dev-dependencies", "build-dependencies"):
        _collect_toml_dep_table(data.get(sec), deps)
    return ("crates", deps, local_names)


def _parse_go_mod(content: str) -> Tuple[str, Dict[str, str], Set[str]]:
    deps: Dict[str, str] = {}
    local_names: Set[str] = set()
    for raw_line in content.splitlines():
        line = raw_line.split("//")[0].strip()
        _process_go_mod_line(line, deps, local_names)
    return ("go", deps, local_names)


def _process_go_mod_line(line: str, deps: Dict[str, str], local_names: Set[str]) -> None:
    if not line or line in ("require (", ")"):
        return
    if line.startswith("module "):
        local_names.add(line.split()[1].strip())
        return
    cleaned = line[len("require ") :].strip() if line.startswith("require ") else line
    parts = cleaned.split()
    if len(parts) >= 2 and "/" in parts[0]:
        deps[parts[0]] = parts[1]


def _parse_composer_json(content: str) -> Tuple[str, Dict[str, str], Set[str]]:
    data = _safe_json_loads(content)
    if not isinstance(data, dict):
        return ("packagist", {}, set())
    local_names = {data["name"]} if isinstance(data.get("name"), str) else set()
    deps: Dict[str, str] = {}
    for sec in ("require", "require-dev"):
        _collect_composer_section(data.get(sec), deps)
    return ("packagist", deps, local_names)


def _collect_composer_section(sec_data: Any, deps: Dict[str, str]) -> None:
    if not isinstance(sec_data, dict):
        return
    for k, v in sec_data.items():
        if k != "php" and not k.startswith("ext-") and isinstance(v, str):
            deps[k] = v


def _parse_csproj(content: str) -> Tuple[str, Dict[str, str], Set[str]]:
    matches = re.findall(
        r'<PackageReference\s+Include=["\']([^"\']+)["\'](?:\s+Version=["\']([^"\']+)["\'])?',
        content,
        flags=re.IGNORECASE,
    )
    return ("nuget", {pkg: (ver or "*") for pkg, ver in matches}, set())


# -----------------------------------------------------------------------------
# Source Code Import Scanners (V(G) <= 10 per function)
# -----------------------------------------------------------------------------
def _iter_source_files(source_dir: Path, suffixes: Set[str]) -> List[Path]:
    if not source_dir.exists():
        return []
    matched: List[Path] = []
    for p in source_dir.rglob("*"):
        if p.is_file() and p.suffix in suffixes and not (set(p.parts) & EXCLUDED_DIRS):
            matched.append(p)
    return matched


def scan_source_imports(source_dir: Path, ecosystem: str) -> Dict[str, List[str]]:
    eco = ecosystem.lower()
    if eco in ("pypi", "python"):
        return _scan_python_imports(source_dir)
    if eco in ("npm", "node"):
        return _scan_node_imports(source_dir)
    if eco in ("pub", "dart", "flutter"):
        return _scan_dart_imports(source_dir)
    return {}


def _scan_python_imports(source_dir: Path) -> Dict[str, List[str]]:
    py_files = _iter_source_files(source_dir, {".py"})
    stdlib = set(getattr(sys, "stdlib_module_names", set())) | PYTHON_STDLIB_EXTRAS
    local_mods = {p.stem for p in py_files} | {p.parent.name for p in py_files if p.name == "__init__.py"}

    imports_map: Dict[str, List[str]] = {}
    for py_file in py_files:
        for top_mod in _extract_py_file_imports(py_file):
            if top_mod not in stdlib and top_mod not in local_mods and not top_mod.startswith("_"):
                mapped = PYTHON_IMPORT_TO_PYPI.get(top_mod.lower(), top_mod)
                imports_map.setdefault(mapped, []).append(str(py_file))
    return imports_map


def _extract_dynamic_call_import(node: ast.Call) -> Optional[str]:
    """Extracts literal module name from importlib.import_module('pkg') or __import__('pkg') ([INF-ASI08-05])."""
    if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
        return None
    mod_arg = node.args[0].value.strip()
    if not mod_arg or mod_arg.startswith("."):
        return None
    func = node.func
    is_dunder = isinstance(func, ast.Name) and func.id == "__import__"
    is_import_mod = (
        isinstance(func, ast.Attribute) and func.attr == "import_module"
    ) or (isinstance(func, ast.Name) and func.id == "import_module")
    return mod_arg.split(".")[0] if (is_dunder or is_import_mod) else None


def _extract_py_file_imports(py_file: Path) -> Set[str]:
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"), filename=str(py_file))
    except SyntaxError:
        return set()

    mods: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(alias.name.split(".")[0] for alias in node.names if alias.name)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            dyn_mod = _extract_dynamic_call_import(node)
            if dyn_mod:
                mods.add(dyn_mod)
    return mods


def _scan_node_imports(source_dir: Path) -> Dict[str, List[str]]:
    js_files = _iter_source_files(source_dir, {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"})
    import_re = re.compile(
        r"""(?:import\s+(?:[^'"]+?\s+from\s+)?['"]([^'"]+)['"]|import\s*\(\s*['"]([^'"]+)['"]\s*\)|require\(\s*['"]([^'"]+)['"]\s*\))"""
    )
    imports_map: Dict[str, List[str]] = {}
    for js_file in js_files:
        text = js_file.read_text(encoding="utf-8", errors="replace")
        for m in import_re.finditer(text):
            pkg = _normalize_node_import(m.group(1) or m.group(2) or m.group(3) or "")
            if pkg:
                imports_map.setdefault(pkg, []).append(str(js_file))
    return imports_map


def _normalize_node_import(raw_imp: str) -> Optional[str]:
    imp = raw_imp.strip()
    if not imp or imp.startswith((".", "/", "~", "@/", "node:")):
        return None
    parts = imp.split("/")
    pkg = f"{parts[0]}/{parts[1]}" if imp.startswith("@") and len(parts) >= 2 else parts[0]
    return None if pkg in NODE_BUILTINS else pkg


def _scan_dart_imports(source_dir: Path) -> Dict[str, List[str]]:
    dart_files = _iter_source_files(source_dir, {".dart"})
    dart_re = re.compile(r"""^\s*(?:import|export)\s+['"]package:([a-zA-Z0-9_]+)/""", re.MULTILINE)
    imports_map: Dict[str, List[str]] = {}
    for dart_file in dart_files:
        text = dart_file.read_text(encoding="utf-8", errors="replace")
        for m in dart_re.finditer(text):
            pkg = m.group(1).strip()
            if pkg not in DART_SDK_PACKAGES:
                imports_map.setdefault(pkg, []).append(str(dart_file))
    return imports_map


def verify_import_parity(
    source_dir: Path,
    ecosystem: str,
    declared_packages: Dict[str, str],
    local_project_names: Set[str],
) -> List[str]:
    imports_map = scan_source_imports(source_dir, ecosystem)
    if not imports_map:
        return []

    norm_declared = {normalize_pkg_name(k, ecosystem) for k in declared_packages}
    norm_declared |= {normalize_pkg_name(k, ecosystem) for k in local_project_names}
    norm_declared |= {k.replace("-", "_") for k in list(norm_declared)}

    errors: List[str] = []
    for imp_pkg, files in sorted(imports_map.items()):
        norm_imp = normalize_pkg_name(imp_pkg, ecosystem)
        if norm_imp not in norm_declared and norm_imp.replace("-", "_") not in norm_declared:
            errors.append(
                f"[UNDECLARED_IMPORT] Package '{imp_pkg}' imported in '{Path(files[0]).name}' "
                f"is NOT declared in the {ecosystem} manifest."
            )
    return errors


# -----------------------------------------------------------------------------
# CLI Orchestration
# -----------------------------------------------------------------------------
def _parse_cli_spec(raw_spec: str) -> Tuple[str, Optional[str]]:
    if "==" in raw_spec:
        k, v = raw_spec.split("==", 1)
        return k.strip(), v.strip()
    if "@" in raw_spec and not raw_spec.startswith("@"):
        k, v = raw_spec.split("@", 1)
        return k.strip(), v.strip()
    return raw_spec.strip(), None


def _run_check_mode(args: argparse.Namespace) -> List[PackageAuditResult]:
    print(f"🔍 Auditing {len(args.check)} requested package(s) on '{args.ecosystem}' registry...")
    results: List[PackageAuditResult] = []
    for raw_spec in args.check:
        pkg_name, ver_spec = _parse_cli_spec(raw_spec)
        results.append(audit_package(args.ecosystem, pkg_name, ver_spec, min_age_days=args.min_age_days))
    return results


def _run_manifest_mode(args: argparse.Namespace) -> Tuple[int, List[PackageAuditResult], List[str]]:
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"❌ Manifest file not found: '{manifest_path}'")
        return 1, [], []

    eco, deps, local_names = parse_manifest(manifest_path)
    if eco == "unknown":
        print(
            f"⚠️ [NEEDS_WEB_AUDIT] Unrecognized manifest '{manifest_path.name}'. "
            "Dispatch `dependency-auditor` subagent with `search_web`."
        )
        return (1 if args.strict else 0), [], []

    print(f"🔍 Auditing {len(deps)} package(s) from '{manifest_path.name}' (ecosystem: {eco})...")
    results = [audit_package(eco, k, v, min_age_days=args.min_age_days) for k, v in deps.items()]
    imp_errors = (
        verify_import_parity(Path(args.scan_imports), eco, deps, local_names) if args.scan_imports else []
    )
    return 0, results, imp_errors


def _print_report(
    results: List[PackageAuditResult], import_errors: List[str], strict: bool
) -> int:
    total_errors = list(import_errors)
    total_warnings: List[str] = []
    web_audit_pkgs: List[str] = []

    for r in results:
        _print_package_line(r)
        total_errors.extend(r.errors)
        total_warnings.extend(r.warnings)
        if r.needs_web_audit:
            web_audit_pkgs.append(f"{r.name} ({r.ecosystem})")

    print("----------------------------------------------------------------------")
    _print_messages("⚠️ Security / Slopsquatting Warning(s):", total_warnings)
    if web_audit_pkgs:
        print(
            f"\n🌐 [ACTION REQUIRED: SUBAGENT WEB AUDIT] Dispatch `dependency-auditor` (Model: 'flash', tool: `search_web`) "
            f"to verify repository legitimacy and module docs for: {', '.join(web_audit_pkgs)}"
        )
    _print_messages("\n❌ Dependency Audit FAILED:", total_errors)

    if total_errors or (total_warnings and strict):
        return 1
    print("\n✅ Dependency audit COMPLETED! All verified packages exist in official registries.")
    return 0


def _print_package_line(r: PackageAuditResult) -> None:
    if r.exists and not r.errors and not r.warnings:
        age_str = f", age: {r.age_days}d" if r.age_days is not None else ""
        print(f"   ✅ {r.name} (latest: {r.latest_version}{age_str})")
    elif r.exists and not r.errors:
        print(f"   ⚠️ {r.name} (latest: {r.latest_version}) -> Flagged for review")
    else:
        print(f"   ❌ {r.name} -> FAILED verification")


def _print_messages(header: str, items: List[str]) -> None:
    if not items:
        return
    print(f"{header} ({len(items)})")
    for item in items:
        print(f"   {item}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Multi-ecosystem Dependency Existence, Anti-Slopsquatting & Import Parity Auditor."
    )
    parser.add_argument("manifest", nargs="?", default=None, help="Path to manifest file.")
    parser.add_argument("--check", nargs="+", default=None, help="Check specific packages before installation.")
    parser.add_argument("--ecosystem", default="pypi", help="Target ecosystem for --check (default: pypi).")
    parser.add_argument("--scan-imports", dest="scan_imports", default=None, help="Source dir for import parity.")
    parser.add_argument("--min-age-days", type=int, default=60, help="Minimum package age in days (default: 60).")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors (exit code 1).")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.check:
        return _print_report(_run_check_mode(args), [], args.strict)
    if args.manifest:
        code, results, imp_errors = _run_manifest_mode(args)
        return code if not results and not imp_errors else _print_report(results, imp_errors, args.strict)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
