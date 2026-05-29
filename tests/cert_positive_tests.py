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

    def test_generated_proof_without_comments_replays_close_true(self):
        proof = """\\problem { true }\n\\proof {\n(branch "dummy ID"\n(rule "closeTrue" (formula "1"))\n)\n}\n"""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'generated.proof'
            path.write_text(proof)
            cert = certificate_from_proof(path)
        self.assertEqual(cert.steps[0].after, 'closed')
        result = CertificateChecker().check_certificate(cert)
        self.assertTrue(result.accepted, result.error)

    def test_opaque_initial_for_functional_obligation_trace(self):
        proof = """\\proofObligation {\n  "name": "opaque"\n}\n\\proof {\n(branch "dummy ID"\n(rule "false_to_not_true" (formula "1"))\n(rule "closeFalse" (formula "1"))\n)\n}\n"""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'opaque.proof'
            path.write_text(proof)
            cert = certificate_from_proof(path)
        self.assertTrue(cert.initial_sequent.startswith('opaque-initial-sequent('))
        self.assertTrue(CertificateChecker().check_certificate(cert).accepted)

if __name__ == '__main__':
    unittest.main()
