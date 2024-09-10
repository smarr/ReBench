from . import none_or_bool


class Denoise(object):

    @classmethod
    def compile(cls, config, defaults):
        use_nice = none_or_bool(config.get("use_nice", defaults.use_nice))
        shield = config.get("shield", defaults.shield)
        scaling_governor = config.get("scaling_governor", defaults.scaling_governor)
        no_turbo = none_or_bool(config.get("no_turbo", defaults.no_turbo))
        minimize_perf_sampling = none_or_bool(
            config.get("minimize_perf_sampling", defaults.minimize_perf_sampling)
        )

        return Denoise(
            use_nice, shield, scaling_governor, no_turbo, minimize_perf_sampling
        )

    def __init__(
        self, use_nice, shield, scaling_governor, no_turbo, minimize_perf_sampling
    ):
        self.use_nice = use_nice
        self.shield = shield
        self.scaling_governor = scaling_governor
        assert no_turbo is None or isinstance(no_turbo, bool)
        self.no_turbo = no_turbo
        self.minimize_perf_sampling = minimize_perf_sampling

    @classmethod
    def default(cls):
        return Denoise(True, "basic", "performance", True, True)

    @classmethod
    def system_default(cls):
        """Do not change settings and rely on system defaults."""
        return Denoise(False, "no_change", "no_change", "no_change", "no_change")

    @property
    def requested_nice(self):
        return self.use_nice

    @property
    def requested_shield(self):
        return self.shield != "no_change"

    @property
    def requested_scaling_governor(self):
        return self.scaling_governor != "no_change"

    @property
    def requested_no_turbo(self):
        return self.no_turbo != "no_change"

    @property
    def requested_minimize_perf_sampling(self):
        return self.minimize_perf_sampling != "no_change"

    def needs_denoise(self):
        return (
            self.requested_nice
            or self.requested_shield
            or self.requested_scaling_governor
            or self.requested_no_turbo
            or self.requested_minimize_perf_sampling
        )

    def as_dict(self):
        return {
            "use_nice": self.use_nice,
            "shield": self.shield,
            "scaling_governor": self.scaling_governor,
            "no_turbo": self.no_turbo,
            "minimize_perf_sampling": self.minimize_perf_sampling,
        }

    @classmethod
    def max_union(cls, a, b):
        """
        Return the combined maximum of the two configurations.
        This is useful to find which denoise features are used across all runs.
        """
        use_nice = a.use_nice or b.use_nice
        shield = b.shield if a.shield == "no_change" else a.shield
        scaling_governor = (
            b.scaling_governor
            if a.scaling_governor == "no_change"
            else a.scaling_governor
        )
        no_turbo = b.no_turbo if a.no_turbo is None else a.no_turbo
        minimize_perf_sampling = a.minimize_perf_sampling or b.minimize_perf_sampling

        return Denoise(
            use_nice, shield, scaling_governor, no_turbo, minimize_perf_sampling
        )
