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

    def test_max_union_default_vs_system_default(self):
        sys_defaults = Denoise.system_default()
        defaults = Denoise.default()

        union = Denoise.max_union_to_get_used_features(sys_defaults, defaults)
        self.assertEqual(union, defaults)

        union = Denoise.max_union_to_get_used_features(defaults, sys_defaults)
        self.assertEqual(union, defaults)

    def test_no_turbo_is_identified_as_used(self):
        sys_defaults = Denoise.system_default()
        new_settings = Denoise.system_default()
        new_settings.no_turbo = True

        union = Denoise.max_union_to_get_used_features(sys_defaults, new_settings)
        self.assertEqual(union, new_settings)

        union = Denoise.max_union_to_get_used_features(new_settings, sys_defaults)
        self.assertEqual(union, new_settings)

        new_settings.no_turbo = False

        union = Denoise.max_union_to_get_used_features(sys_defaults, new_settings)
        self.assertEqual(union, new_settings)

        union = Denoise.max_union_to_get_used_features(new_settings, sys_defaults)
        self.assertEqual(union, new_settings)
        self.assertTrue(new_settings.requested_no_turbo)
