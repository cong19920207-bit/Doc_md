# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("REPO_ROOT", str(ROOT))
os.environ.setdefault("ALIASES_PATH", str(ROOT / "site" / "kb-api" / "feature_aliases.json"))
os.environ.setdefault("DATA_DIR", str(ROOT / "site" / "kb-api" / "tests" / ".tmp-data"))
os.environ.setdefault("KB_AUTH_MEMORY", "1")
os.environ.setdefault("KB_PBKDF2_ITERATIONS", "1000")
os.environ.setdefault("KB_BOOTSTRAP_USER", "admin")
os.environ.setdefault("KB_BOOTSTRAP_PASSWORD", "admin-test-pass")


class DefaultRouter:
    """默认替身 Router：不关心分路的旧用例一律按知识查询，不打外网。"""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def route(self, original, l1_turns, cfg, carry=None):
        self.calls.append({"original": original, "l1_turns": list(l1_turns), "carry": carry})
        return {
            "route": "knowledge_query",
            "requires_history": False,
            "confidence": 1.0,
            "reason": "测试默认",
            "extra_keys": [],
        }


class DefaultTaskPreparer:
    """默认替身任务准备：原句即一个可执行的查询任务，不打外网。"""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def prepare(self, original, l1_turns, route, requires_history, cfg, carry=None):
        self.calls.append({"original": original, "route": route, "carry": carry})
        return {
            "tasks": [{
                "task_id": "T1", "goal": original, "mode": "查询", "scope": "", "constraints": [],
                "depends_on": [], "check": "ready", "gap_ids": [],
            }],
            "excluded": [],
            "information_gaps": [],
            "response_constraint": "",
            "extra_keys": [],
        }


class DefaultChecker:
    """默认替身证据检查：一律通过，不打外网。"""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def check(self, original, brief, query, constraint, draft, evidence, cfg):
        self.calls.append(draft)
        return {"check_status": "pass", "issues": [], "conflict": False}

    async def repair(self, original, brief, query, constraint, draft, issues, evidence, cfg):
        return draft


@pytest.fixture(autouse=True)
def _default_router(monkeypatch):
    main = sys.modules.get("app.main")
    if main is not None:
        monkeypatch.setattr(main, "router", DefaultRouter())
        monkeypatch.setattr(main, "task_preparer", DefaultTaskPreparer())
        monkeypatch.setattr(main, "evidence_checker", DefaultChecker())

        # 启动时不连真实向量库做记忆回填；需要的用例自行调用
        async def _no_memory_startup():
            return None

        monkeypatch.setattr(main, "_startup_memory", _no_memory_startup)
        # 旧用例默认不启用追溯（预算未配置 → 只用 L1，保持「暂不支持查找」说明）；M6 用例自行打开
        monkeypatch.setattr(main.settings, "RECALL_MAX_CALLS", 0)
    yield
