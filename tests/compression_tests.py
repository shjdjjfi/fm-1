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

if __name__ == '__main__':
    unittest.main()
