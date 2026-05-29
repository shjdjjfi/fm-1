# RustyDL-Cert Certificate Format

RustyDL-Cert uses stable, pretty-printed JSON so certificates are readable and
reviewable in artifact evaluation.  The current format identifier is
`rustydl-cert-v1`; compressed certificates use `rustydl-cert-v1-compressed`.

## Full certificates

A full certificate records the RustyKeY/RustyDL proof trace as independently
replayable textual sequent steps:

```json
{
  "format": "rustydl-cert-v1",
  "program": ".",
  "specification": "...",
  "initial_sequent": "x = z ==> <{ ... }>(y = z)",
  "rustydl_version": "rusty-key-0.1.0",
  "proof_id": "...",
  "steps": [
    {
      "step_id": 0,
      "rule": "assignment_update",
      "parent": null,
      "before": "...",
      "after": "...",
      "premises": ["..."],
      "conclusion": "...",
      "substitution": {},
      "side_conditions": ["formula:2"],
      "generated_updates": ["{x := e}"],
      "branch_ids": ["root"],
      "child_step_ids": [1],
      "source_location": "proof:12",
      "rule_category": "rust_program_rule",
      "branch_closed": false,
      "replay_digest": "..."
    }
  ],
  "closed_leaves": ["root"],
  "metadata": {
    "num_steps": 1,
    "num_branches": 1,
    "num_closed_leaves": 0
  }
}
```

Each step records the rule identifier, textual premise and conclusion sequents,
substitutions, side conditions, generated update fragments, branch identifiers,
parent and child step identifiers, source proof location, rule category, branch
closure flag, and a SHA-256 replay digest over the canonical step payload.

## Replay precision

The current artifact is intentionally non-invasive because the RustyKeY proof
engine is distributed as a JAR.  It therefore records proof applications by
parsing `.proof` files emitted by RustyKeY.

* **Exact replay fields:** rule names, before/after textual sequents, parent and
  child step identifiers, substitutions present in the proof trace, side-condition
  attributes, branch closure flags, and replay digests.
* **Conservative replay fields:** the checker validates textual sequent shape and
  schema-level compatibility rather than rebuilding the full internal KeY term
  graph.
* **Trusted-boundary fields:** source-level Rust parsing, proof search, taclet
  execution, and rich arithmetic simplification are not trusted by the checker;
  their emitted steps are replayed against an independent whitelist of supported
  schemas. Unsupported rules are rejected as `UnsupportedRule`.

## Rule categories

`rule_category` is one of:

1. `rust_program_rule`
2. `dynamic_logic_rule`
3. `structural_rule`
4. `arithmetic_rule`
5. `simplification_rule`
6. `loop_invariant_rule`
7. `branch_closing_rule`

The recorder infers categories from RustyKeY rule names.  The checker uses these
categories for compression-safe deterministic simplification blocks.

## Compressed certificates

Compressed certificates dictionary-encode repeated sequents and summarize
consecutive deterministic simplification/arithmetic steps as macro steps:

```json
{
  "format": "rustydl-cert-v1-compressed",
  "initial_sequent": "...",
  "dictionary": {"seq_0": "...", "seq_1": "..."},
  "substitution_table": {"subst_0": {}},
  "side_condition_table": {"side_0": ["formula:2"]},
  "macro_steps": [
    {
      "macro_rule": "deterministic_simplification_block",
      "from_ref": "seq_0",
      "to_ref": "seq_1",
      "elided_steps": 3,
      "step_ids": [4, 5, 6],
      "rule_sequence": ["simplifyUpdate1", "applyOnPV", "add_zero_right"],
      "step_digests": ["...", "...", "..."]
    }
  ],
  "essential_steps": [],
  "closed_leaves": ["root"],
  "metadata": {"compression_ratio": 2.0}
}
```

The compressed checker validates dictionary references, macro arity, rule support,
and that deterministic simplification macros contain only replayable deterministic
rules. Essential nontrivial RustyDL steps retain full step payloads and digests.
