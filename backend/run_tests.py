#!/usr/bin/env python
"""Run tests and report results."""
import sys
import subprocess
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--timeout=30"],
    cwd=str(BACKEND_DIR)
)

sys.exit(result.returncode)
