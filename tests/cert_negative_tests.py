import copy
import unittest
from pathlib import Path

from cert.recorder import certificate_from_proof
from checker.checker import CertificateChecker

ROOT = Path(__file__).resolve().parents[1]

class CertificateNegativeTests(unittest.TestCase):
    def setUp(self):
        self.cert = certificate_from_proof(ROOT / 'examples/paper/example5.proof')
        self.checker = CertificateChecker()

    def assertRejected(self, cert, initial=None):
        result = self.checker.check_certificate(cert, initial)
        self.assertFalse(result.accepted)
        self.assertTrue(result.error)

    def test_modified_rule_id_rejected(self):
        cert = copy.deepcopy(self.cert)
        cert.steps[0].rule = 'not_a_supported_rule'
        self.assertRejected(cert)

    def test_modified_substitution_rejected(self):
        cert = copy.deepcopy(self.cert)
        cert.steps[0].substitution['x'] = 'y'
        self.assertRejected(cert)

    def test_deleted_side_condition_rejected(self):
        cert = copy.deepcopy(self.cert)
        cert.steps[-1].side_conditions = []
        cert.steps[-1].seal()
        self.assertRejected(cert)

    def test_modified_branch_closing_rejected(self):
        cert = copy.deepcopy(self.cert)
        cert.steps[-1].side_conditions = ['closure:false']
        cert.steps[-1].seal()
        self.assertRejected(cert)

    def test_modified_initial_sequent_rejected(self):
        self.assertRejected(self.cert, self.cert.initial_sequent + ' corrupted')

if __name__ == '__main__':
    unittest.main()
