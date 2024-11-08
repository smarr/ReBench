from . import none_or_bool


class Denoise(object):

    @classmethod
    def compile(cls, config, defaults):
        use_nice = none_or_bool(config.get("use_nice", defaults.use_nice))
        shield = config.get("shield", defaults.shield)
        scaling_governor = config.get("scaling_governor", defaults.scaling_governor)
        set_no_turbo = none_or_bool(config.get("set_no_turbo", defaults.set_no_turbo))
        minimize_perf_sampling = none_or_bool(
            config.get("minimize_perf_sampling", defaults.minimize_perf_sampling)
        )

        return Denoise(
            use_nice, shield, scaling_governor, set_no_turbo, minimize_perf_sampling
        )

    def __init__(
        self, use_nice, shield, scaling_governor, set_no_turbo, minimize_perf_sampling
    ):
        self.use_nice = use_nice
        self.shield = shield
        self.scaling_governor = scaling_governor
        self.set_no_turbo = set_no_turbo
        self.minimize_perf_sampling = minimize_perf_sampling

    @classmethod
    def default(cls):
        return Denoise(True, "basic", "performance", True, True)

    def as_dict(self):
        return {
            "use_nice": self.use_nice,
            "shield": self.shield,
            "scaling_governor": self.scaling_governor,
            "set_no_turbo": self.set_no_turbo,
            "minimize_perf_sampling": self.minimize_perf_sampling,
        }
