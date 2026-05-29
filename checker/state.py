"""Replay proof-state bookkeeping."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from cert.model import CertificateStep

@dataclass
class SequentReplayState:
    initial_sequent: str
    current_by_branch: Dict[str, str] = field(default_factory=dict)
    closed_branches: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.current_by_branch.setdefault("root", self.initial_sequent)

    def branch_key(self, step: CertificateStep) -> str:
        return "/".join(step.branch_ids) if step.branch_ids else "root"

    def expected_before(self, step: CertificateStep) -> str:
        key = self.branch_key(step)
        if key in self.current_by_branch:
            return self.current_by_branch[key]
        return self.initial_sequent if step.parent is None else ""

    def apply(self, step: CertificateStep) -> None:
        key = self.branch_key(step)
        # Generated RustyKeY proofs often call the single root branch "dummy ID".
        # When the first replay step targets such a branch, transfer the initial
        # root obligation to that branch instead of leaving a spurious root goal open.
        if key != "root" and key not in self.current_by_branch:
            # A fresh branch in the textual KeY proof denotes that the parent
            # goal has been split/replaced by this child branch.  The certificate
            # does not contain explicit branch-open events, so transfer replay to
            # the newly observed branch and avoid retaining stale parent goals.
            self.current_by_branch.clear()
        if step.branch_closed:
            self.closed_branches.append(key)
            self.current_by_branch.pop(key, None)
        else:
            self.current_by_branch[key] = step.after
