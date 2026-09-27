# -*- coding: utf-8 -*-
"""证书只保存；点启用才标记 HTTPS。私钥不回显。"""
from __future__ import annotations

import json
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.serialization import load_pem_private_key, Encoding, PublicFormat

from . import settings

log_name = "kb-api.tls"


class TlsStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root else settings.DATA_DIR

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

    def status(self) -> dict:
        p = self._paths()
        has_pending = p["pending_cert"].is_file() and p["pending_key"].is_file()
        has_live = p["cert"].is_file() and p["key"].is_file()
        enabled = self.is_enabled()
        return {
            "enabled": enabled,
            "scheme": "http",
            "redirect_https": False,
            "has_cert": has_pending or has_live,
            "has_key": has_pending or has_live,
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
        if not cert_path.is_file() or not key_path.is_file():
            raise ValueError("还没有可启用的证书")
        cert_pem = cert_path.read_text(encoding="utf-8")
        key_pem = key_path.read_text(encoding="utf-8")
        self._validate(cert_pem, key_pem)
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
