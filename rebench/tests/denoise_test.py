from ..model.denoise import Denoise
from .rebench_test_case import ReBenchTestCase
from ..denoise_client import minimize_noise


class DenoiseTest(ReBenchTestCase):

    def setUp(self):
        super(DenoiseTest, self).setUp()
        self._set_path(__file__)

    def test_minimize(self):
        result = minimize_noise(Denoise.system_default(), False, False, self.ui)

        self.assertEqual(result, Denoise.system_default())
        assert not result.needs_denoise()
