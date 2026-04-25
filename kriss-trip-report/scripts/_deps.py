"""Dependency helpers for KRISS trip report scripts."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType


def _add_codex_runtime_site_packages() -> None:
    """Make Codex desktop's bundled Python packages visible when using system Python."""
    home = Path.home()
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    candidates = [
        home / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python" / "Lib" / "site-packages",
        home / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python" / "lib" / version / "site-packages",
    ]
    for candidate in candidates:
        if candidate.exists():
            path = str(candidate)
            if path not in sys.path:
                sys.path.append(path)


def import_or_install(module_name: str, package_name: str | None = None) -> ModuleType:
    """Import a module, using bundled packages first and pip as a last resort."""
    _add_codex_runtime_site_packages()
    try:
        return importlib.import_module(module_name)
    except ImportError as first_error:
        package = package_name or module_name.split(".", 1)[0]
        if os.environ.get("KRISS_TRIP_REPORT_NO_AUTO_INSTALL"):
            raise RuntimeError(
                f"Missing Python dependency '{package}'. Install it with: "
                f"{sys.executable} -m pip install {package}"
            ) from first_error
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except Exception as install_error:
            raise RuntimeError(
                f"Missing Python dependency '{package}' and automatic installation failed. "
                f"Install it with: {sys.executable} -m pip install {package}"
            ) from install_error
        return importlib.import_module(module_name)
