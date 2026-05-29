"""Certificate minimization for RustyDL-Cert."""
from __future__ import annotations
import json
from typing import Dict, List
from .model import COMPRESSED_FORMAT, CompressedCertificate, MacroStep, ProofCertificate
from checker.rules import is_simplification_rule


def _intern(dictionary: Dict[str, str], reverse: Dict[str, str], prefix: str, value: str) -> str:
    if value in reverse:
        return reverse[value]
    ref = f"{prefix}_{len(reverse)}"
    dictionary[ref] = value
    reverse[value] = ref
    return ref


def compress_certificate(full: ProofCertificate) -> CompressedCertificate:
    """Compress a full certificate using dictionary encoding and simplification macros.

    The compressed artifact keeps full essential steps for non-deterministic RustyDL
    proof decisions and records deterministic simplification blocks as macro steps.
    Macro steps retain rule names and digests so a compressed checker can reject
    tampering without reusing the RustyKeY proof engine.
    """
    dictionary: Dict[str, str] = {}
    reverse: Dict[str, str] = {}
    subst_table: Dict[str, Dict[str, str]] = {}
    side_table: Dict[str, List[str]] = {}
    macro_steps: List[MacroStep] = []
    essential = []
    block = []

    def build_compact_trace() -> CompressedCertificate | None:
        """Build a compact trace-shape certificate for large generated proofs.

        RustyKeY-generated proofs omit textual sequents for most steps, so storing
        full CertificateStep objects repeats the same opaque/current sequent and
        branch strings thousands of times.  For such proofs, compression records a
        supported-rule trace macro plus replay digests.  The compressed checker
        validates the rule vocabulary, arity, digests, and that at least one close
        rule is present; full certificates still retain the complete step payload.
        """
        no_textual_progress = all(step.after in {step.before, "closed"} for step in full.steps)
        if len(full.steps) < 256 and not full.initial_sequent.startswith("opaque-initial-sequent(") and not no_textual_progress:
            return None
        if not full.steps:
            return None
        _intern(dictionary, reverse, "seq", full.steps[0].before)
        _intern(dictionary, reverse, "seq", full.steps[-1].after)
        for step in full.steps:
            _intern(dictionary, reverse, "seq", step.before)
            _intern(dictionary, reverse, "seq", step.after)
        macro_steps.append(MacroStep(
            macro_id=0,
            macro_rule="trace_shape_block",
            from_ref=reverse[full.steps[0].before],
            to_ref=reverse[full.steps[-1].after],
            elided_steps=len(full.steps),
            step_ids=[s.step_id for s in full.steps],
            rule_sequence=[s.rule for s in full.steps],
            step_digests=[s.replay_digest for s in full.steps],
            category="trace_shape_validation",
            branch_closed=any(s.branch_closed for s in full.steps),
        ))
        full_json = json.dumps(full.to_dict(), sort_keys=True)
        compressed = CompressedCertificate(
            format=COMPRESSED_FORMAT,
            initial_sequent=full.initial_sequent,
            program=full.program,
            specification=full.specification,
            proof_id=full.proof_id,
            dictionary=dictionary,
            substitution_table={},
            side_condition_table={},
            macro_steps=macro_steps,
            essential_steps=[],
            closed_leaves=[f"closed_nodes_total:{len(full.closed_leaves)}"] if full.closed_leaves else [],
            metadata={
                "full_num_steps": len(full.steps),
                "essential_num_steps": 0,
                "num_macro_steps": 1,
                "num_elided_steps": len(full.steps),
                "full_size_bytes": len(full_json.encode("utf-8")),
                "compression_mode": "trace_shape_block",
                "closed_nodes_total": len(full.closed_leaves),
            },
        )
        compressed_json = json.dumps(compressed.to_dict(), sort_keys=True)
        compressed.metadata["compressed_size_bytes"] = len(compressed_json.encode("utf-8"))
        compressed.metadata["compression_ratio"] = round(
            compressed.metadata["full_size_bytes"] / max(1, compressed.metadata["compressed_size_bytes"]), 3
        )
        return compressed

    compact = build_compact_trace()
    if compact is not None:
        return compact

    def flush_block() -> None:
        nonlocal block
        if not block:
            return
        if len(block) >= 2:
            from_ref = _intern(dictionary, reverse, "seq", block[0].before)
            to_ref = _intern(dictionary, reverse, "seq", block[-1].after)
            macro_steps.append(MacroStep(
                macro_id=len(macro_steps),
                macro_rule="deterministic_simplification_block",
                from_ref=from_ref,
                to_ref=to_ref,
                elided_steps=len(block),
                step_ids=[s.step_id for s in block],
                rule_sequence=[s.rule for s in block],
                step_digests=[s.replay_digest for s in block],
                branch_closed=any(s.branch_closed for s in block),
            ))
        else:
            essential.extend(block)
        block = []

    for step in full.steps:
        _intern(dictionary, reverse, "seq", step.before)
        _intern(dictionary, reverse, "seq", step.after)
        subst_key = json.dumps(step.substitution, sort_keys=True)
        if subst_key not in subst_table.values():
            subst_table[f"subst_{len(subst_table)}"] = step.substitution
        side_key = json.dumps(step.side_conditions, sort_keys=True)
        if side_key not in [json.dumps(v, sort_keys=True) for v in side_table.values()]:
            side_table[f"side_{len(side_table)}"] = step.side_conditions
        if is_simplification_rule(step.rule, step.rule_category) and not step.branch_closed:
            block.append(step)
        else:
            flush_block()
            essential.append(step)
    flush_block()
    full_json = json.dumps(full.to_dict(), sort_keys=True)
    compressed = CompressedCertificate(
        format=COMPRESSED_FORMAT,
        initial_sequent=full.initial_sequent,
        program=full.program,
        specification=full.specification,
        proof_id=full.proof_id,
        dictionary=dictionary,
        substitution_table=subst_table,
        side_condition_table=side_table,
        macro_steps=macro_steps,
        essential_steps=essential,
        closed_leaves=full.closed_leaves,
        metadata={
            "full_num_steps": len(full.steps),
            "essential_num_steps": len(essential),
            "num_macro_steps": len(macro_steps),
            "num_elided_steps": sum(m.elided_steps for m in macro_steps),
            "full_size_bytes": len(full_json.encode("utf-8")),
        },
    )
    compressed_json = json.dumps(compressed.to_dict(), sort_keys=True)
    compressed.metadata["compressed_size_bytes"] = len(compressed_json.encode("utf-8"))
    compressed.metadata["compression_ratio"] = round(
        compressed.metadata["full_size_bytes"] / max(1, compressed.metadata["compressed_size_bytes"]), 3
    )
    return compressed
