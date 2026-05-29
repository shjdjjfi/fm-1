"""Certificate recorder for RustyKeY proof artifacts.

The shipped RustyKeY implementation is distributed as a JAR, so this recorder is
non-invasive: it consumes `.proof` files emitted by RustyKeY and turns each
recorded `(rule ...) // sequent` line into a replayable certificate step.  When a
source `.key` file is available the recorder extracts the initial problem text as
certificate context.
"""
from __future__ import annotations

import re
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .model import CertificateMetadata, CertificateStep, FORMAT, ProofCertificate

RULE_RE = re.compile(r'\(rule\s+"(?P<rule>[^"]+)"(?P<attrs>.*?)\)\s*(?://\s*(?P<seq>.*))?$')
ATTR_RE = re.compile(r'\((?P<key>[A-Za-z0-9_]+)\s+"(?P<value>[^"]*)"\)')
BRANCH_RE = re.compile(r'\(branch\s+"(?P<branch>[^"]+)"')
PROBLEM_RE = re.compile(r'\\problem\s*\{(?P<body>.*?)\}', re.DOTALL)
PROGRAM_SOURCE_RE = re.compile(r'\\programSource\s+"(?P<src>[^"]+)"')
PROOF_OBLIGATION_RE = re.compile(r'\\proofObligation\s*\{(?P<body>.*?)\}', re.DOTALL)

SIMPLIFICATION_RULES = {
    "sequentialToParallel2", "simplifyUpdate1", "simplifyUpdate2", "applyOnElementary",
    "applyOnRigidTerm", "applyOnPV", "applyOnRigidFormula", "empty_modality",
    "simple_expr_stmt", "add_zero_right", "add_zero_left", "times_zero_1", "times_zero_2",
    "add_literals", "polySimp_elimSub", "polySimp_pullOutFactor1b", "polySimp_mulComm0",
    "polySimp_addComm0", "polySimp_addAssoc", "polySimp_sepNegMonomial",
}
ARITHMETIC_PREFIXES = ("polySimp", "add_", "times_", "mul_", "inEq", "eqSimp")
RUST_PROGRAM_KEYWORDS = (
    "assignment", "assign", "read", "write", "borrow", "reference", "array", "tuple",
    "enum", "case", "loop", "invariant", "return", "if", "method", "while", "match",
)


def classify_rule(rule: str) -> str:
    lower = rule.lower()
    if rule.startswith("close") or "close" in lower:
        return "branch_closing_rule"
    if rule in SIMPLIFICATION_RULES or "simplify" in lower or "update" in lower:
        return "simplification_rule"
    if rule.startswith(ARITHMETIC_PREFIXES) or any(tok in lower for tok in ["arith", "literal", "zero", "integer"]):
        return "arithmetic_rule"
    if any(k in lower for k in RUST_PROGRAM_KEYWORDS):
        if "loop" in lower or "invariant" in lower:
            return "loop_invariant_rule"
        return "rust_program_rule"
    if any(k in lower for k in ["and", "or", "imp", "not", "cut", "weaken", "contract"]):
        return "structural_rule"
    return "dynamic_logic_rule"


def parse_attrs(attr_text: str) -> Dict[str, str]:
    return {m.group("key"): m.group("value") for m in ATTR_RE.finditer(attr_text)}


def extract_context(text: str) -> Tuple[str, str, str]:
    problem = PROBLEM_RE.search(text)
    obligation = PROOF_OBLIGATION_RE.search(text)
    source = PROGRAM_SOURCE_RE.search(text)
    initial = " ".join(problem.group("body").split()) if problem else ""
    spec = " ".join(obligation.group("body").split()) if obligation else initial
    program = source.group("src") if source else ""
    return program, spec, initial


class CertificateRecorder:
    """Accumulates proof-rule applications into a certificate."""

    def __init__(self, program: str = "", specification: str = "", initial_sequent: str = "") -> None:
        self.program = program
        self.specification = specification
        self.initial_sequent = initial_sequent
        self.steps: List[CertificateStep] = []
        self.closed_leaves: List[str] = []
        self.branch_stack: List[str] = ["root"]

    def record_rule(self, rule: str, before: str, after: str, attrs: Dict[str, str], line_no: int) -> CertificateStep:
        step_id = len(self.steps)
        parent = step_id - 1 if step_id > 0 else None
        branch_ids = list(self.branch_stack) or ["root"]
        side_conditions = [f"{k}:{v}" for k, v in sorted(attrs.items())]
        if rule == "closeTrue" and not any(sc.startswith("closure:true") for sc in side_conditions):
            side_conditions.append("closure:true")
        elif rule == "closeFalse" and not any(sc.startswith("closure:false") for sc in side_conditions):
            side_conditions.append("closure:false")
        elif rule == "close" and not any(sc.startswith("assumesSeqFormula:") for sc in side_conditions):
            side_conditions.append("closure:syntactic")
        generated_updates = []
        if "{" in after and ":=" in after:
            generated_updates.append(after[after.find("{"): after.rfind("}") + 1] if "}" in after else after)
        step = CertificateStep(
            step_id=step_id,
            rule=rule,
            parent=parent,
            before=before,
            after=after,
            premises=[before] if before else [],
            conclusion=after,
            substitution={k: v for k, v in attrs.items() if k in {"subst", "inst", "var", "schemaVar"}},
            side_conditions=side_conditions,
            generated_updates=generated_updates,
            branch_ids=branch_ids,
            source_location=f"proof:{line_no}",
            rule_category=classify_rule(rule),
            branch_closed=(rule.startswith("close") or after.strip() == "closed"),
        )
        step.seal()
        if self.steps:
            self.steps[-1].child_step_ids.append(step_id)
            self.steps[-1].seal()
        if step.branch_closed:
            self.closed_leaves.append("/".join(branch_ids) or f"step:{step_id}")
        self.steps.append(step)
        return step

    def to_certificate(self, rustydl_version: str = "rusty-key-0.1.0", proof_id: Optional[str] = None) -> ProofCertificate:
        pid = proof_id or sha256((self.initial_sequent + str(len(self.steps))).encode()).hexdigest()[:16]
        metadata = CertificateMetadata(
            num_steps=len(self.steps),
            num_branches=len({tuple(s.branch_ids) for s in self.steps}) if self.steps else 0,
            num_closed_leaves=len(self.closed_leaves),
        )
        return ProofCertificate(
            format=FORMAT,
            program=self.program,
            specification=self.specification,
            initial_sequent=self.initial_sequent or (self.steps[0].before if self.steps else ""),
            rustydl_version=rustydl_version,
            proof_id=pid,
            steps=self.steps,
            closed_leaves=self.closed_leaves,
            metadata=metadata,
        )


def certificate_from_proof(proof_path: Path, key_path: Optional[Path] = None) -> ProofCertificate:
    proof_text = proof_path.read_text(encoding="utf-8")
    context_text = key_path.read_text(encoding="utf-8") if key_path and key_path.exists() else proof_text
    program, spec, initial = extract_context(context_text)
    # Proof-obligation .key files do not contain an explicit \problem block;
    # RustyKeY materializes the initial sequent in the generated .proof file.
    # Fall back to that materialized sequent so source-level benchmarks receive
    # non-empty replay state instead of an empty placeholder.
    if not initial:
        generated_program, generated_spec, generated_initial = extract_context(proof_text)
        program = program or generated_program
        spec = spec or generated_spec
        initial = generated_initial
    if not initial:
        # Functional proof-obligation files generated by RustyKeY may omit the
        # materialized sequent entirely and store only rule applications.  Use a
        # stable opaque sequent token so the independent checker can still replay
        # rule order, rule support, branching, closure, and compression metadata.
        initial = f"opaque-initial-sequent({proof_path.name})"
    recorder = CertificateRecorder(program=program, specification=spec, initial_sequent=initial)
    current = initial
    for line_no, line in enumerate(proof_text.splitlines(), start=1):
        branch = BRANCH_RE.search(line)
        if branch:
            recorder.branch_stack = [f"{branch.group('branch')}@{line_no}"]
        match = RULE_RE.search(line)
        if not match:
            continue
        rule = match.group("rule")
        attrs = parse_attrs(match.group("attrs") or "")
        after = (match.group("seq") or "").strip()
        # Automatically generated RustyKeY .proof files record rule names and
        # positions but omit the human-readable // sequent comments present in
        # manual proofs.  Keep the current sequent for such conservative replay
        # steps and materialize closing rules as a closed leaf.
        if not after:
            after = "closed" if rule.startswith("close") else current
        before = current
        recorder.record_rule(rule, before, after, attrs, line_no)
        current = after
    return recorder.to_certificate(proof_id=sha256(str(proof_path).encode()).hexdigest()[:16])
