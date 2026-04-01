#!/usr/bin/env python
"""Run tests and report results."""
import sys
import subprocess

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--timeout=30"],
    cwd=r"c:\Users\andre\Desktop\Coach-AI-Project\ProjectB"
)

sys.exit(result.returncode)
