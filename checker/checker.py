"""Small independent checker for RustyDL-Cert full and compressed certificates."""
from __future__ import annotations
from typing import Dict, List

from cert.model import COMPRESSED_FORMAT, FORMAT, CompressedCertificate, ProofCertificate
from .result import CheckResult
from .rules import (
    check_sequent_text,
    is_simplification_rule,
    is_supported_rule,
    side_conditions_well_formed,
    substitution_well_typed,
    syntactic_close,
)
from .state import SequentReplayState


class CertificateChecker:
    """Replay checker that validates certificate steps without invoking RustyKeY."""

    def check_certificate(self, cert: ProofCertificate, initial_sequent: str | None = None) -> CheckResult:
        if cert.format != FORMAT:
            return CheckResult(False, f"UnsupportedFormat: {cert.format}")
        initial = initial_sequent if initial_sequent is not None else cert.initial_sequent
        if initial != cert.initial_sequent:
            return CheckResult(False, "InitialSequentMismatch: certificate initial sequent differs from supplied initial sequent")
        if not cert.steps:
            return CheckResult(False, "EmptyCertificate")
        state = SequentReplayState(initial)
        by_id = {}
        for idx, step in enumerate(cert.steps):
            if step.step_id != idx:
                return CheckResult(False, f"StepOrderError: expected step_id {idx}, got {step.step_id}", idx)
            by_id[step.step_id] = step
            if not step.verify_digest():
                return CheckResult(False, f"ReplayDigestMismatch at step {idx}", idx)
            if not is_supported_rule(step.rule):
                return CheckResult(False, f"UnsupportedRule: {step.rule} at step {idx}", idx)
            if step.parent is not None and step.parent not in by_id:
                return CheckResult(False, f"ParentNotChecked: {step.parent} at step {idx}", idx)
            if step.parent is None and idx != 0:
                return CheckResult(False, f"UnexpectedRootStep at step {idx}", idx)
            if idx == 0 and step.parent is not None:
                return CheckResult(False, "FirstStepMustHaveNullParent", idx)
            expected = state.expected_before(step)
            if expected and step.before != expected:
                return CheckResult(False, f"SequentChainMismatch at step {idx}", idx)
            if not check_sequent_text(step.before) or not check_sequent_text(step.after):
                return CheckResult(False, f"MalformedSequent at step {idx}", idx)
            if not substitution_well_typed(step.substitution):
                return CheckResult(False, f"MalformedSubstitution at step {idx}", idx)
            if not side_conditions_well_formed(step.side_conditions, step.branch_closed):
                return CheckResult(False, f"MalformedSideCondition at step {idx}", idx)
            if step.branch_closed and step.after != "closed" and step.rule not in {"close", "closeTrue", "closeFalse", "branch_close"}:
                return CheckResult(False, f"InvalidClosureRule at step {idx}", idx)
            if step.rule == "closeTrue" and "closure:true" not in step.side_conditions:
                return CheckResult(False, f"InvalidBranchClosingCondition at step {idx}", idx)
            if step.rule == "closeFalse" and "closure:false" not in step.side_conditions:
                return CheckResult(False, f"InvalidBranchClosingCondition at step {idx}", idx)
            if step.rule in {"close", "branch_close"} and not syntactic_close(step.before, step.side_conditions):
                return CheckResult(False, f"InvalidBranchClosingCondition at step {idx}", idx)
            state.apply(step)
        if len(state.closed_branches) != len(cert.closed_leaves):
            return CheckResult(False, "ClosedLeafMetadataMismatch", len(cert.steps), len(state.closed_branches))
        if state.current_by_branch:
            return CheckResult(False, "OpenGoalsRemain: " + ",".join(sorted(state.current_by_branch)), len(cert.steps), len(state.closed_branches))
        return CheckResult(True, checked_steps=len(cert.steps), closed_leaves=len(state.closed_branches))

    def check_compressed_certificate(self, cert: CompressedCertificate, initial_sequent: str | None = None) -> CheckResult:
        if cert.format != COMPRESSED_FORMAT:
            return CheckResult(False, f"UnsupportedFormat: {cert.format}")
        initial = initial_sequent if initial_sequent is not None else cert.initial_sequent
        if initial != cert.initial_sequent:
            return CheckResult(False, "InitialSequentMismatch: compressed certificate initial sequent differs")
        for macro in cert.macro_steps:
            if macro.from_ref not in cert.dictionary or macro.to_ref not in cert.dictionary:
                return CheckResult(False, f"DictionaryReferenceMissing in macro {macro.macro_id}")
            if macro.elided_steps != len(macro.step_ids) or macro.elided_steps != len(macro.rule_sequence):
                return CheckResult(False, f"MacroArityMismatch in macro {macro.macro_id}")
            for rule in macro.rule_sequence:
                if not is_supported_rule(rule):
                    return CheckResult(False, f"UnsupportedRule: {rule} in macro {macro.macro_id}")
                if macro.macro_rule == "deterministic_simplification_block" and not is_simplification_rule(rule, ""):
                    return CheckResult(False, f"NonDeterministicRuleInSimplificationMacro: {rule}")
            if len(macro.step_digests) != len(macro.step_ids):
                return CheckResult(False, f"MacroDigestMismatch in macro {macro.macro_id}")
        # Essential steps retain their full payloads and digests, but their surrounding
        # deterministic steps may have been summarized as macros.  Therefore the
        # compressed checker validates each essential step locally instead of requiring
        # contiguous full-certificate step identifiers.
        for step in cert.essential_steps:
            if not step.verify_digest():
                return CheckResult(False, f"ReplayDigestMismatch at essential step {step.step_id}")
            if not is_supported_rule(step.rule):
                return CheckResult(False, f"UnsupportedRule: {step.rule} at essential step {step.step_id}")
            if not check_sequent_text(step.before) or not check_sequent_text(step.after):
                return CheckResult(False, f"MalformedSequent at essential step {step.step_id}")
            if step.rule == "closeTrue" and "closure:true" not in step.side_conditions:
                return CheckResult(False, f"InvalidBranchClosingCondition at essential step {step.step_id}")
            if step.rule == "closeFalse" and "closure:false" not in step.side_conditions:
                return CheckResult(False, f"InvalidBranchClosingCondition at essential step {step.step_id}")
            if step.rule in {"close", "branch_close"} and not syntactic_close(step.before, step.side_conditions):
                return CheckResult(False, f"InvalidBranchClosingCondition at essential step {step.step_id}")
        if not cert.closed_leaves:
            return CheckResult(False, "OpenGoalsRemain: compressed certificate has no closed leaves")
        checked = sum(m.elided_steps for m in cert.macro_steps) + len(cert.essential_steps)
        return CheckResult(True, checked_steps=checked, closed_leaves=len(cert.closed_leaves))
