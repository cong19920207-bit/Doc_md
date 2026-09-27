# -*- coding: utf-8 -*-
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("REPO_ROOT", str(ROOT))
os.environ.setdefault("ALIASES_PATH", str(ROOT / "site" / "kb-api" / "feature_aliases.json"))
os.environ.setdefault("DATA_DIR", str(ROOT / "site" / "kb-api" / "tests" / ".tmp-data"))
os.environ.setdefault("KB_AUTH_MEMORY", "1")
os.environ.setdefault("KB_PBKDF2_ITERATIONS", "1000")
os.environ.setdefault("KB_BOOTSTRAP_USER", "admin")
os.environ.setdefault("KB_BOOTSTRAP_PASSWORD", "admin-test-pass")
