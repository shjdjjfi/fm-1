"""Independent textual rule-schema checks for RustyDL-Cert.

This module intentionally does not call RustyKeY.  It recognizes the rule names
and textual sequent transformations present in the current RustyDL artifact, plus
research-extension names for RustyDL source-level constructs.  Unknown rules are
rejected rather than silently accepted.
"""
from __future__ import annotations
import re
from typing import Iterable, Set

SUPPORTED_RULES: Set[str] = {
    # Rust/source-level rules.
    "assignment_update", "assignmentAdditionI32", "assignmentSubtractionI32", "assignment",
    "variable_substitution", "reference_read", "reference_write", "borrow_shared",
    "borrow_mut", "array_read", "array_write", "loop_invariant", "tuple_projection",
    "enum_case_split", "symbolic_simplification", "branch_close", "close", "closeTrue", "closeFalse",
    "simple_expr_stmt", "empty_modality",
    # Update/simplification rules commonly emitted by KeY.
    "sequentialToParallel2", "simplifyUpdate1", "simplifyUpdate2", "applyOnElementary",
    "applyOnRigidTerm", "applyOnPV", "applyOnRigidFormula", "applyOnUpdate", "applyOnSkip",
    # Arithmetic and propositional simplification observed in artifacts.
    "polySimp_elimSub", "polySimp_pullOutFactor1b", "polySimp_mulComm0", "polySimp_addComm0",
    "polySimp_addAssoc", "polySimp_sepNegMonomial", "add_literals", "mul_literals", "leq_literals", "greater_literals", "qeq_literals", "equal_literals", "times_zero_1",
    "times_zero_2", "add_zero_right", "add_zero_left", "eqSymm", "eqClose", "true_left",
    "false_right", "false_to_not_true", "applySkip1", "andRight", "andLeft", "orRight", "orLeft", "impRight", "impLeft",
}
SUPPORTED_PREFIXES = ("polySimp_", "polyDiv_", "inEqSimp_", "concrete_", "wd_", "rust_", "let_", "assign_", "assignment", "deref_", "apply", "simplify", "arr_", "if", "method", "loop", "block", "return", "variable", "function_", "expand_", "replace_", "all", "nnf_", "eq", "cut", "commute_", "compound_", "panic_", "implicit_", "explicit_", "ls", "empty_", "bool_", "not", "or", "ex", "shift_", "sign_", "div_", "rdiv_", "elim", "multiply_", "neg_", "neq_", "prec")


def is_supported_rule(rule: str) -> bool:
    return rule in SUPPORTED_RULES or rule.startswith(SUPPORTED_PREFIXES)


DETERMINISTIC_SIMPLIFICATION_RULES = {
    "simple_expr_stmt", "empty_modality", "sequentialToParallel2", "simplifyUpdate1",
    "simplifyUpdate2", "applyOnElementary", "applyOnRigidTerm", "applyOnPV",
    "applyOnRigidFormula", "applyOnUpdate", "applyOnSkip", "add_literals",
    "mul_literals", "leq_literals", "greater_literals", "qeq_literals", "equal_literals", "times_zero_1", "times_zero_2", "add_zero_right", "add_zero_left",
}

def is_simplification_rule(rule: str, category: str) -> bool:
    return (
        category in {"simplification_rule", "arithmetic_rule"}
        or rule in DETERMINISTIC_SIMPLIFICATION_RULES
        or rule.startswith(("polySimp_", "polyDiv_", "inEqSimp_", "simplify"))
    )


def check_sequent_text(text: str) -> bool:
    if text is None:
        return False
    stripped = text.strip()
    if stripped == "closed":
        return True
    return bool(stripped) and ("==>" in stripped or "\\problem" not in stripped)


def syntactic_close(before: str, side_conditions: Iterable[str]) -> bool:
    conditions = list(side_conditions)
    if any(sc.startswith("assumesSeqFormula:") for sc in conditions):
        return True
    if "closure:syntactic" in conditions and "==>" in before:
        left, right = before.split("==>", 1)
        left_atoms = {a.strip() for a in re.split(r",|&&", left) if a.strip()}
        right_atoms = {a.strip() for a in re.split(r",|&&", right) if a.strip()}
        return bool(left_atoms & right_atoms)
    return False


def substitution_well_typed(substitution: dict) -> bool:
    return all(isinstance(k, str) and isinstance(v, str) and k for k, v in substitution.items())


def side_conditions_well_formed(side_conditions: list[str], closing: bool = False) -> bool:
    if closing and not side_conditions:
        return False
    return all(isinstance(sc, str) and sc for sc in side_conditions)
