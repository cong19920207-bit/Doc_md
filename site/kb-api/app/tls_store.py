# -*- coding: utf-8 -*-
"""证书只保存；点启用才标记 HTTPS。私钥不回显。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.serialization import load_pem_private_key, Encoding, PublicFormat

from . import settings

log_name = "kb-api.tls"


class TlsStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root else settings.TLS_DIR

    def migrate_legacy(self, legacy_root: Path) -> None:
        """一次性复制已知 TLS 文件；保留旧卷，后续启动不覆盖新证书。"""
        self.root.mkdir(parents=True, exist_ok=True)
        marker = self.root / ".legacy-migrated"
        if marker.is_file() or self.root.resolve() == legacy_root.resolve():
            return
        names = ("cert.pem", "key.pem", "pending-cert.pem", "pending-key.pem", "state.json", "https.enabled")
        contents = {}
        for name in names:
            source, target = legacy_root / name, self.root / name
            if source.is_symlink() or target.is_symlink():
                raise RuntimeError("TLS 迁移拒绝符号链接")
            if source.is_file():
                contents[name] = source.read_bytes()
                if target.exists() and target.read_bytes() != contents[name]:
                    raise RuntimeError("TLS 新旧目录内容冲突，未覆盖已有证书")
        for name, content in contents.items():
            target = self.root / name
            if not target.exists():
                temporary = self.root / (".migrate-" + name)
                temporary.write_bytes(content)
                temporary.chmod(0o600)
                temporary.replace(target)
        marker.write_text("1\n", encoding="utf-8")

    def _paths(self) -> dict[str, Path]:
        self.root.mkdir(parents=True, exist_ok=True)
        return {
            "pending_cert": self.root / "pending-cert.pem",
            "pending_key": self.root / "pending-key.pem",
            "cert": self.root / "cert.pem",
            "key": self.root / "key.pem",
            "enabled": self.root / "https.enabled",
            "state": self.root / "state.json",
        }

    def is_enabled(self) -> bool:
        return self._paths()["enabled"].is_file()

    def _state(self) -> dict:
        p = self._paths()["state"]
        try:
            data = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
            return data if isinstance(data, dict) else {}
        except Exception:  # noqa: BLE001
            return {}

    def _write_state(self, **fields) -> None:
        data = self._state()
        data.update(fields)
        self._paths()["state"].write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def status(self) -> dict:
        p = self._paths()
        has_pending = p["pending_cert"].is_file() and p["pending_key"].is_file()
        has_live = p["cert"].is_file() and p["key"].is_file()
        enabled = self.is_enabled()
        # STEP-A18：上传只保存；已保存但与正在使用的不同（或未启用）时标「待启用」
        pending = has_pending and not (
            enabled and has_live
            and p["pending_cert"].read_bytes() == p["cert"].read_bytes()
            and p["pending_key"].read_bytes() == p["key"].read_bytes()
        )
        st = self._state()
        return {
            "enabled": enabled,
            "scheme": "http",
            "redirect_https": False,
            "has_cert": has_pending or has_live,
            "has_key": has_pending or has_live,
            "pending": pending,
            "last_enable_error": st.get("last_enable_error"),
            "last_enable_error_at": st.get("last_enable_error_at"),
            "port_note": "对外端口不是 80/443 时，即使已启用也不强制跳转 HTTPS",
        }

    def save_upload(self, cert_pem: str, key_pem: str) -> dict:
        cert_pem = str(cert_pem or "")
        key_pem = str(key_pem or "")
        if "-----BEGIN" not in cert_pem or "-----BEGIN" not in key_pem:
            raise ValueError("请上传 PEM 证书和私钥")
        p = self._paths()
        p["pending_cert"].write_text(cert_pem, encoding="utf-8")
        p["pending_key"].write_text(key_pem, encoding="utf-8")
        return self.status()

    def enable(self) -> dict:
        p = self._paths()
        cert_path = p["pending_cert"] if p["pending_cert"].is_file() else p["cert"]
        key_path = p["pending_key"] if p["pending_key"].is_file() else p["key"]
        try:
            if not cert_path.is_file() or not key_path.is_file():
                raise ValueError("还没有可启用的证书")
            cert_pem = cert_path.read_text(encoding="utf-8")
            key_pem = key_path.read_text(encoding="utf-8")
            self._validate(cert_pem, key_pem)
        except ValueError as exc:
            # 启用失败：开关不动，只留下失败原因，页面如实显示
            self._write_state(last_enable_error=str(exc),
                              last_enable_error_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            raise
        p["cert"].write_text(cert_pem, encoding="utf-8")
        p["key"].write_text(key_pem, encoding="utf-8")
        p["enabled"].write_text("1", encoding="utf-8")
        p["state"].write_text(json.dumps({"enabled": True}, ensure_ascii=False), encoding="utf-8")
        return self.status()

    def disable(self) -> dict:
        p = self._paths()
        if p["enabled"].is_file():
            p["enabled"].unlink()
        p["state"].write_text(json.dumps({"enabled": False}, ensure_ascii=False), encoding="utf-8")
        return self.status()

    @staticmethod
    def _validate(cert_pem: str, key_pem: str) -> None:
        try:
            cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"))
            key = load_pem_private_key(key_pem.encode("utf-8"), password=None)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"证书无效：{exc}") from exc
        cert_pub = cert.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        key_pub = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        if cert_pub != key_pub:
            raise ValueError("证书与私钥不匹配")
