import copy
import unittest
from pathlib import Path

from cert.compressor import compress_certificate
from cert.recorder import certificate_from_proof
from checker.checker import CertificateChecker

ROOT = Path(__file__).resolve().parents[1]

class CompressionTests(unittest.TestCase):
    def test_compressed_certificate_replays(self):
        cert = certificate_from_proof(ROOT / 'examples/paper/example5.proof')
        compressed = compress_certificate(cert)
        result = CertificateChecker().check_compressed_certificate(compressed)
        self.assertTrue(result.accepted, result.error)
        self.assertGreater(compressed.metadata['num_elided_steps'], 0)

    def test_modified_compressed_macro_rejected(self):
        cert = certificate_from_proof(ROOT / 'examples/paper/example5.proof')
        compressed = compress_certificate(cert)
        bad = copy.deepcopy(compressed)
        bad.macro_steps[0].rule_sequence[0] = 'assignment_update'
        result = CertificateChecker().check_compressed_certificate(bad)
        self.assertFalse(result.accepted)

    def test_large_generated_trace_uses_compact_macro(self):
        cert = certificate_from_proof(ROOT / 'results/generated/example1.proof') if (ROOT / 'results/generated/example1.proof').exists() else None
        if cert is None:
            self.skipTest('generated example1 proof not available')
        compressed = compress_certificate(cert)
        self.assertEqual(compressed.metadata.get('compression_mode'), 'trace_shape_block')
        result = CertificateChecker().check_compressed_certificate(compressed)
        self.assertTrue(result.accepted, result.error)

if __name__ == '__main__':
    unittest.main()
