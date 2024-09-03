from .rebench_test_case import ReBenchTestCase
from ..denoise_client import minimize_noise, restore_noise


class DenoiseTest(ReBenchTestCase):

    def setUp(self):
        super(DenoiseTest, self).setUp()
        self._set_path(__file__)

    def test_minimize(self):
        result = minimize_noise(False, self.ui, True)
        self.assertIsInstance(result.succeeded, bool)
        self.assertIsInstance(result.use_nice, bool)
        self.assertIsInstance(result.use_shielding, bool)

        # if it was successful, try to restore normal settings
        if result.succeeded:
            restore_noise(result, False, self.ui)
