"""Stable JSON reader and writer for RustyDL-Cert artifacts."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Union
from .model import CompressedCertificate, ProofCertificate


def write_certificate(cert: Union[ProofCertificate, CompressedCertificate], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cert.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def read_certificate(path: Path) -> ProofCertificate:
    return ProofCertificate.from_dict(json.loads(path.read_text(encoding="utf-8")))


def read_compressed_certificate(path: Path) -> CompressedCertificate:
    return CompressedCertificate.from_dict(json.loads(path.read_text(encoding="utf-8")))
