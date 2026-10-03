# -*- coding: utf-8 -*-
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]


def test_qa_first_tab_and_no_process_panel():
    html = (ROOT / "site" / "feature-interaction" / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "site" / "feature-interaction" / "qa.js").read_text(encoding="utf-8")
    tabs = re.findall(r'<button class="tab[^"]*" data-view="([^"]+)"[^>]*>(.*?)</button>', html, re.S)
    labels = [re.sub(r'<[^>]+>', '', t[1]).strip() for t in tabs]
    # 2026-10-03 用户明确要求知识问答排第一；图标不影响可读标签。
    assert labels == ["知识问答", "客户端 ↔ 后台", "客户端交叉", "文档索引"]
    assert 'id="qaWorkspace"' in html
    assert 'id="kbWorkspace"' in html
    assert 'id="qaProcess"' not in html
    assert 'id="qaProcess"' not in js
    assert "data-qa-rounds" not in html
    assert "data-qa-heatmap" not in html
    assert "data-qa-config" not in html
    assert "data-qa-reindex" not in html
    assert 'id="qaHealth"' in html
    assert 'id="qaTopActions"' in html
    assert "退出" in html
    assert "修改密码" in html
    # C22：允许空状态 chips；静态 HTML 可不含 qa-chip，但 qa.js 必须能渲染
    assert "qa-chip" in js
    assert "data-qa-chip" in js


def test_compose_bind_localhost_and_no_3306():
    text = (ROOT / "site" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "qdrant:" in text
    assert "kb-api:" in text
    assert "mysql:" in text
    assert "0.0.0.0" not in text
    ports = re.findall(r"127\.0\.0\.1:(?:\$\{[A-Z0-9_]+:-)?(\d+)\}?:\d+", text)
    host_ports = list(ports)
    assert ports
    assert "3306" not in host_ports
    assert "3307" not in host_ports
    assert "18765" in host_ports
    assert "18766" in host_ports
