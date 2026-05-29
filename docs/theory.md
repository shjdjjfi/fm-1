# RustyDL-Cert Theory and Soundness Argument

RustyDL-Cert is not a new Rust verifier and does not aim to improve proof
automation. Instead, it turns source-level RustyDL proofs into independently
checkable proof certificates. The key contribution is a replayable certificate
language, a small trusted checker, and a compression-preserving replay mechanism
that reduces the trusted computing base of Rust source-level deductive
verification.

## Objects

Let `Seq` be the set of RustyDL sequents. In the artifact implementation, sequents
are represented by RustyKeY textual sequents; in the mathematical model they stand
for the corresponding RustyDL formulas and program modalities.

A certificate step is a tuple

```text
s = (id, r, parent, before, after, premises, conclusion,
     subst, side, updates, branches, children, closed)
```

where `r` is a RustyDL/KeY rule identifier, `before` is the selected open goal,
`after` is the produced goal or `closed`, `subst` instantiates rule schema
variables, `side` contains side conditions, and `branches` identifies the proof
branch to update.

## Certificate step relation

The step relation is written

```text
Γ ⊢step s : σ ⇝ σ'
```

and means that, under rule-schema environment `Γ`, step `s` transforms replay
state `σ` into replay state `σ'`.  The checker establishes this relation by:

1. checking that `r` is a supported RustyDL rule schema;
2. checking that `before` is the current open sequent of the referenced branch;
3. checking that `subst` is well formed;
4. checking that side conditions required by the schema are present;
5. checking the textual shape of `before` and `after`;
6. replacing the open branch by `after`, or marking it closed if `closed = true`.

Unsupported rules do not inhabit the relation; the checker returns
`UnsupportedRule` instead of accepting them conservatively.

## Checker transition relation

A replay state is a finite map from branch identifiers to open sequents, plus a
set of closed leaves:

```text
σ = (open : Branch ⇀ Seq, closed : P(Branch)).
```

The transition relation for a certificate prefix is the reflexive-transitive
closure of the step relation:

```text
Γ ⊢cert [] : σ ⇝ σ
Γ ⊢step s : σ ⇝ σ1    Γ ⊢cert ss : σ1 ⇝ σ2
------------------------------------------------
Γ ⊢cert s :: ss : σ ⇝ σ2
```

The initial replay state contains exactly one open branch, `root`, labelled by the
certificate's `initial_sequent`.

## Leaf closure condition

A full certificate is accepted only if replay terminates with no open branches:

```text
accept(C) iff Γ ⊢cert C.steps : ({root ↦ C.initial}, ∅) ⇝ (∅, L)
             and L = C.closed_leaves.
```

Branch-closing rules require either an explicit assumption-reference side
condition (`assumesSeqFormula`) or a checker-recognized syntactic closure marker.
Thus the checker is not a proof search procedure; it validates that the certificate
contains enough information to justify closure.

## Theorem 1: Rule Replay Soundness

**Statement.** If a certificate step is accepted by the checker, then the
corresponding RustyDL rule application is sound.

**Argument.** The checker accepts a step only when the rule identifier belongs to
its trusted schema table, the current branch sequent matches the recorded premise,
the conclusion has a well-formed sequent shape, substitutions are well formed, and
required side conditions are present.  The trusted schema table contains only
RustyDL structural, source-program, update, arithmetic-simplification, and
branch-closing schemas whose soundness is part of the RustyDL calculus.  Therefore
an accepted transition preserves validity of the replay state.

## Theorem 2: Certificate Soundness

**Statement.** If a full certificate is accepted by the checker, then the original
RustyDL sequent is valid.

**Argument.** By induction over the certificate steps.  The base state contains the
initial sequent.  The induction step follows from Theorem 1: each accepted rule
application transforms valid proof obligations into sound premises.  Acceptance
requires that all leaves are closed.  Closed leaves are valid by the branch-closing
schema, so the root sequent is valid by backward soundness of the replayed proof
tree.

## Theorem 3: Compression Preservation

**Statement.** If a compressed certificate is accepted by the checker, then it
denotes a valid expansion into a full RustyDL proof.

**Argument.** A compressed macro step records a source sequent reference, target
sequent reference, arity, rule sequence, and replay digests of the elided full
steps. The compressed checker accepts deterministic simplification blocks only
when every elided rule is in the deterministic replay subset and all dictionary
references and arities are consistent.  Expanding each macro by its recorded rule
sequence and retaining essential steps yields a full certificate accepted by the
full-step relation.  Theorem 2 then gives validity of the root sequent.

## Trusted computing base

The trusted base of RustyDL-Cert consists of:

* the JSON parser and certificate data-model code;
* the independent checker modules in `checker/`;
* the textual rule-schema table and simple side-condition checker;
* optional external arithmetic/SMT backends if enabled in future work.

The RustyKeY proof search engine, taclet executor, simplifier, and Rust compiler
front-end are certificate producers, not certificate checkers.  Bugs in those
components can only lead to accepted results if they produce a certificate that
passes the independent replay relation.

## Current limitations

The current prototype replays RustyKeY textual sequents rather than deserializing
KeY's internal term graph. Complex arithmetic side conditions are checked by a
simple structural checker; richer arithmetic replay can be added by plugging in an
SMT backend without changing the certificate format.

## Checker granularity and conservative replay

The implemented checker is intentionally small, so its replay relation is stratified:

1. **Precise replay** covers certificate integrity, rule identity, parent ordering,
   current-branch sequencing, substitution well-formedness, explicit closure side
   conditions, and digest checks.
2. **Schema-level textual replay** covers RustyDL source/update rules whose proof
   traces include textual sequents. The checker validates that the known schema is
   applied to the current textual goal and that the resulting goal is chained.
3. **Conservative trace-shape replay** covers RustyKeY-generated traces that omit
   textual sequents. For these traces the checker uses stable opaque sequents and
   validates known rule families, branch/closure structure, step ids, and digests.
4. **Arithmetic replay** is currently a small built-in side-condition backend over
   known arithmetic simplification rule families. A future SMT backend could refine
   this layer without changing the certificate language.

This stratification is part of the trusted-boundary claim: RustyDL-Cert reduces the
trusted base by replacing proof search and taclet execution with an independently
checked certificate, but it does not claim to machine-check the full KeY term graph
for every generated rule in the current prototype.

## Compression status

Compression uses two mechanisms. Small proofs with textual sequents use dictionary
sharing plus deterministic simplification macro steps. Large RustyKeY-generated
proofs use a compact `trace_shape_block`, which avoids repeating opaque/current
sequents and branch strings thousands of times. This makes the large benchmark
certificates smaller while keeping the compressed checker honest about the more
conservative replay granularity.
