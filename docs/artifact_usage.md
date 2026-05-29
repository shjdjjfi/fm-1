# RustyDL-Cert Artifact Usage

## Generate and check a certificate

```bash
make verify-cert EXAMPLE=example5
```

Equivalent explicit commands:

```bash
./rustydl-cert from-proof examples/paper/example5.proof --out out/example5.full.json
./rustydl-cert check out/example5.full.json
./rustydl-cert compress out/example5.full.json --out out/example5.compressed.json
./rustydl-cert check-compressed out/example5.compressed.json
```

For `.key` files, `verify` invokes the RustyKeY JAR and then records the emitted
proof:

```bash
./rustydl-cert verify examples/binary-search/binary-search.key --emit-cert out/binary.full.json
```

## Tests

```bash
make cert-tests
```

The test suite contains positive replay tests, negative tampering tests, and
compressed-certificate tests.

## Benchmarks

```bash
make cert-benchmarks
```

Benchmark output is written to:

* `results/cert_benchmark.csv`
* `results/cert_benchmark.md`

If the local environment lacks the Rust compiler wrapper needed by RustyKeY, some
`.key` benchmarks may fail during proof production. Existing `.proof` artifacts
still exercise the certificate recorder, checker, and compressor.
