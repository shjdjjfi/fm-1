# RustyDL-Cert Implementation Summary

## Modified and added files

RustyDL-Cert adds a modular Python extension around the existing RustyDL/RustyKeY
artifact without modifying the shipped RustyKeY JAR or Rust examples.

Added modules:

* `cert/model.py` — stable full and compressed certificate data structures.
* `cert/recorder.py` — non-invasive recorder that extracts proof steps from
  RustyKeY `.proof` files.
* `cert/io.py` — stable JSON reader/writer.
* `cert/compressor.py` — dictionary encoding and deterministic simplification
  macro compression.
* `cert/stats.py` — certificate and trusted-checker statistics helpers.
* `checker/checker.py` — independent full and compressed certificate checker.
* `checker/rules.py` — supported rule schemas, deterministic simplification set,
  side-condition and substitution checks.
* `checker/state.py` — replay proof-state tracking.
* `checker/result.py` — checker result type.
* `rustydl-cert` — command-line interface.
* `scripts/run_cert_benchmarks.py` — benchmark wrapper.
* `scripts/collect_checker_loc.py` — trusted checker LOC collector.
* `scripts/corrupt_certificate_for_negative_tests.py` — negative-test certificate
  corrupter.
* `tests/cert_positive_tests.py` — positive replay tests.
* `tests/cert_negative_tests.py` — negative tampering tests.
* `tests/compression_tests.py` — compressed certificate tests.
* `docs/theory.md` — FM-style soundness argument.
* `docs/certificate_format.md` — certificate language reference.
* `docs/artifact_usage.md` — artifact usage notes.
* `results/cert_benchmark.csv` and `results/cert_benchmark.md` — reproducible
  benchmark tables.
* `Makefile` — convenience targets for certificate generation, tests, and
  benchmarks.

The root `README.md` now contains a RustyDL-Cert section with motivation,
pipeline, trusted boundary, commands, tests, supported subset, and limitations.

## Repository inspection findings

* RustyKeY proof rule applications are represented in generated `.proof` files as
  `(rule "...")` entries under a `\proof` block. The executable proof engine is
  shipped as `rusty-key-0.1.0-exe.jar`.
* Sequents are represented textually in `.key`/`.proof` files with KeY-style
  antecedent/succedent syntax such as `x = z ==> <{ ... }>(y = z)`.
* Proof trees/proof nodes are represented in `.proof` files by nested `(branch
  "...")` blocks containing ordered rule applications.
* Taclet/rule-application records are the readable `(rule ...)` entries emitted by
  RustyKeY.
* Examples live in `examples/paper` and `examples/binary-search`.
* Existing artifact execution is documented in `README.md` and `run_all_tests.sh`;
  RustyKeY is invoked with `java -jar rusty-key-0.1.0-exe.jar`.

## Currently supported RustyDL rule families

The checker supports the rule names and families needed for the current artifact
prototype:

* assignment/update replay (`assignment`, `assignment_update`,
  `assignmentAdditionI32`, `assignmentSubtractionI32`);
* variable substitution and KeY update simplification (`simplifyUpdate*`,
  `applyOn*`, `sequentialToParallel2`);
* reference, dereference, shared borrow, and mutable borrow rules (`assign_*`,
  `deref_*`, `reference_read`, `reference_write`, `borrow_shared`, `borrow_mut`);
* array, tuple, enum, and loop-invariant rule identifiers used as RustyDL source
  rule schemas;
* deterministic symbolic simplification and arithmetic normalization rules,
  including `polySimp_*` and `inEqSimp_*` prefixes;
* branch closing by `close`, `closeTrue`, explicit `assumesSeqFormula`, or a
  syntactic closure marker.

## Currently unsupported rules

Rules not in the checker whitelist or supported prefixes are rejected with
`UnsupportedRule`. Full internal KeY term-graph replay, complete arithmetic proof
checking, and SMT-backed side-condition discharge are not implemented in this
prototype.

## How to run tests

```bash
make cert-tests
```

or directly:

```bash
python3 -m unittest discover -s tests -p '*tests.py'
```

## How to reproduce experiments

```bash
make cert-benchmarks
```

This writes:

* `results/cert_benchmark.csv`
* `results/cert_benchmark.md`

If the host environment lacks the Rust compiler wrapper required by RustyKeY, some
`.key` examples may fail during proof production. Existing `.proof` examples still
exercise certificate generation, replay, compression, and compressed replay.

## Trusted computing base

The RustyDL-Cert trusted computing base is the JSON parser, the `cert/` data-model
and I/O code, and the independent checker under `checker/`. RustyKeY proof search,
KeY taclet execution, simplification, and Rust HIR extraction are certificate
producers and are not called by the checker.

## Next extensions

Future work can add a typed RustyDL term parser for exact internal sequent replay,
a stronger arithmetic/SMT side-condition backend, richer branch-tree reconstruction
for highly branching proofs, and direct in-engine certificate logging if a source
build of RustyKeY is available.
