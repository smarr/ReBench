from unittest import TestCase

from ..denoise import DenoiseResult
from ..environment import determine_source_details, determine_environment, init_environment
from ..ui import TestDummyUI


class ReBenchTestCase(TestCase):

    def test_source_details(self):
        details = determine_source_details()
        self.assertEqual(len(details['commitId']), 40)
        self.assertGreater(len(details['committerName']), 0)
        self.assertGreater(len(details['committerEmail']), 0)
        self.assertGreater(len(details['authorName']), 0)
        self.assertGreater(len(details['authorEmail']), 0)
        self.assertGreater(len(details['commitMsg']), 0)

        self.assertGreater(len(details['branchOrTag']), 0)

        self.assertGreaterEqual(len(details['repoURL']), 0)

    def test_environment(self):
        init_environment(DenoiseResult(True, "", False, False, {}), TestDummyUI())
        env = determine_environment()

        self.assertGreater(len(env['userName']), 0)
        self.assertGreater(len(env['hostName']), 0)
        self.assertGreater(len(env['osType']), 0)
        self.assertGreater(len(env['cpu']), 0)

        self.assertTrue('manualRun' in env)
        self.assertGreater(env['memory'], 0)
        self.assertGreater(env['clockSpeed'], 0)

        self.assertGreaterEqual(len(env['software']), 3)
