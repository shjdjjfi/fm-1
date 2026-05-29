"""Checker result types."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

@dataclass
class CheckResult:
    accepted: bool
    error: str = ""
    checked_steps: int = 0
    closed_leaves: int = 0
    warnings: List[str] = field(default_factory=list)

    def exit_code(self) -> int:
        return 0 if self.accepted else 1
