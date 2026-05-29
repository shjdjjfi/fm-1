"""Stable JSON data structures for RustyDL proof certificates.

The module deliberately stores sequents as RustyKeY textual sequents.  This
keeps the certificate format independent from the large KeY implementation while
still providing enough structure for replay checks over rule order, branch
closure, side conditions, substitutions, and supported textual rule schemas.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from hashlib import sha256
from typing import Any, Dict, List, Optional
import json

FORMAT = "rustydl-cert-v1"
COMPRESSED_FORMAT = "rustydl-cert-v1-compressed"


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_payload(payload: Dict[str, Any]) -> str:
    return sha256(stable_json(payload).encode("utf-8")).hexdigest()


@dataclass
class CertificateStep:
    step_id: int
    rule: str
    parent: Optional[int]
    before: str
    after: str
    premises: List[str] = field(default_factory=list)
    conclusion: str = ""
    substitution: Dict[str, str] = field(default_factory=dict)
    side_conditions: List[str] = field(default_factory=list)
    generated_updates: List[str] = field(default_factory=list)
    branch_ids: List[str] = field(default_factory=list)
    child_step_ids: List[int] = field(default_factory=list)
    source_location: Optional[str] = None
    rule_category: str = "structural_rule"
    branch_closed: bool = False
    replay_digest: str = ""

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "rule": self.rule,
            "parent": self.parent,
            "before": self.before,
            "after": self.after,
            "premises": self.premises,
            "conclusion": self.conclusion,
            "substitution": self.substitution,
            "side_conditions": self.side_conditions,
            "generated_updates": self.generated_updates,
            "branch_ids": self.branch_ids,
            "child_step_ids": self.child_step_ids,
            "source_location": self.source_location,
            "rule_category": self.rule_category,
            "branch_closed": self.branch_closed,
        }

    def seal(self) -> "CertificateStep":
        self.replay_digest = digest_payload(self.canonical_payload())
        return self

    def verify_digest(self) -> bool:
        return self.replay_digest == digest_payload(self.canonical_payload())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CertificateStep":
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CertificateMetadata:
    num_steps: int = 0
    num_branches: int = 0
    num_closed_leaves: int = 0
    producer: str = "rustydl-cert proof-file recorder"
    checker_contract: str = "textual RustyKeY sequent replay with independent schema checks"
    exact_replay_fields: List[str] = field(default_factory=lambda: [
        "rule", "before", "after", "parent", "child_step_ids", "branch_closed",
        "side_conditions", "substitution", "generated_updates", "replay_digest",
    ])
    conservative_replay_fields: List[str] = field(default_factory=lambda: [
        "RustyKeY textual sequent shape", "source_location inferred from proof order",
    ])
    unsupported_rule_policy: str = "reject with UnsupportedRule"


@dataclass
class ProofCertificate:
    format: str
    program: str
    specification: str
    initial_sequent: str
    rustydl_version: str
    proof_id: str
    steps: List[CertificateStep]
    closed_leaves: List[str]
    metadata: CertificateMetadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format,
            "program": self.program,
            "specification": self.specification,
            "initial_sequent": self.initial_sequent,
            "rustydl_version": self.rustydl_version,
            "proof_id": self.proof_id,
            "steps": [s.to_dict() for s in self.steps],
            "closed_leaves": self.closed_leaves,
            "metadata": asdict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProofCertificate":
        return cls(
            format=data["format"],
            program=data.get("program", ""),
            specification=data.get("specification", ""),
            initial_sequent=data.get("initial_sequent", ""),
            rustydl_version=data.get("rustydl_version", "unknown"),
            proof_id=data.get("proof_id", ""),
            steps=[CertificateStep.from_dict(s) for s in data.get("steps", [])],
            closed_leaves=data.get("closed_leaves", []),
            metadata=CertificateMetadata(**data.get("metadata", {})),
        )


@dataclass
class MacroStep:
    macro_id: int
    macro_rule: str
    from_ref: str
    to_ref: str
    elided_steps: int
    step_ids: List[int]
    rule_sequence: List[str]
    step_digests: List[str]
    category: str = "deterministic_simplification_block"
    branch_closed: bool = False


@dataclass
class CompressedCertificate:
    format: str
    initial_sequent: str
    program: str
    specification: str
    proof_id: str
    dictionary: Dict[str, str]
    substitution_table: Dict[str, Dict[str, str]]
    side_condition_table: Dict[str, List[str]]
    macro_steps: List[MacroStep]
    essential_steps: List[CertificateStep]
    closed_leaves: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format,
            "initial_sequent": self.initial_sequent,
            "program": self.program,
            "specification": self.specification,
            "proof_id": self.proof_id,
            "dictionary": self.dictionary,
            "substitution_table": self.substitution_table,
            "side_condition_table": self.side_condition_table,
            "macro_steps": [asdict(m) for m in self.macro_steps],
            "essential_steps": [s.to_dict() for s in self.essential_steps],
            "closed_leaves": self.closed_leaves,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompressedCertificate":
        return cls(
            format=data["format"],
            initial_sequent=data.get("initial_sequent", ""),
            program=data.get("program", ""),
            specification=data.get("specification", ""),
            proof_id=data.get("proof_id", ""),
            dictionary=data.get("dictionary", {}),
            substitution_table=data.get("substitution_table", {}),
            side_condition_table=data.get("side_condition_table", {}),
            macro_steps=[MacroStep(**m) for m in data.get("macro_steps", [])],
            essential_steps=[CertificateStep.from_dict(s) for s in data.get("essential_steps", [])],
            closed_leaves=data.get("closed_leaves", []),
            metadata=data.get("metadata", {}),
        )
