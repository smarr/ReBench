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

    def test_max_union(self):
        sys_defaults = Denoise.system_default()
        defaults = Denoise.default()

        union = Denoise.max_union(sys_defaults, defaults)
        self.assertEqual(union, defaults)

        union = Denoise.max_union(defaults, sys_defaults)
        self.assertEqual(union, defaults)
