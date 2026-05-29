import tempfile
import unittest
from pathlib import Path

from cert.io import write_certificate
from cert.recorder import certificate_from_proof
from checker.checker import CertificateChecker

ROOT = Path(__file__).resolve().parents[1]

class CertificatePositiveTests(unittest.TestCase):
    def test_existing_manual_proof_replays(self):
        cert = certificate_from_proof(ROOT / 'examples/paper/example5.proof')
        result = CertificateChecker().check_certificate(cert)
        self.assertTrue(result.accepted, result.error)
        self.assertGreater(result.checked_steps, 0)

    def test_json_round_trip(self):
        cert = certificate_from_proof(ROOT / 'examples/paper/example5.proof')
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'cert.json'
            write_certificate(cert, path)
            self.assertIn('rustydl-cert-v1', path.read_text())

if __name__ == '__main__':
    unittest.main()
