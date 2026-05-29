import csv
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'example1', 'example2', 'example3', 'example5', 'example6',
    'example7-and-8', 'example9', 'example10', 'binary-search',
}
REQUIRED_FIELDS = [
    'num_rule_steps', 'num_branches', 'num_closed_leaves', 'full_cert_size_kb',
    'compressed_cert_size_kb', 'compression_ratio', 'checker_time_ms',
    'compressed_checker_time_ms', 'trusted_checker_loc',
]

@unittest.skipUnless(os.environ.get('RUSTYDL_CERT_RUN_BENCHMARK_TEST') == '1', 'set RUSTYDL_CERT_RUN_BENCHMARK_TEST=1 to run slow benchmark integration test')
class BenchmarkIntegrationTests(unittest.TestCase):
    def test_all_benchmarks_pass(self):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run([str(ROOT / 'rustydl-cert'), 'benchmark', '--out', td], cwd=ROOT, check=True)
            rows = list(csv.DictReader((Path(td) / 'cert_benchmark.csv').open()))
        self.assertEqual(EXPECTED, {row['example'] for row in rows})
        for row in rows:
            self.assertEqual(row['verification_success'], 'True', row)
            for field in REQUIRED_FIELDS:
                self.assertTrue(row[field], f'{row["example"]} missing {field}')

if __name__ == '__main__':
    unittest.main()
