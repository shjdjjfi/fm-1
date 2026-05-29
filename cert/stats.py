"""Statistics helpers for certificates and checker code."""
from __future__ import annotations
from pathlib import Path
from typing import Iterable
def file_size_kb(path: Path) -> float:
    return round(path.stat().st_size / 1024.0, 3) if path.exists() else 0.0


def trusted_checker_loc(paths: Iterable[Path] = (Path("checker"),)) -> int:
    count = 0
    for root in paths:
        for path in root.rglob("*.py"):
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    count += 1
    return count
