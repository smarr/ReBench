from typing import TYPE_CHECKING, Union

from . import none_or_bool

if TYPE_CHECKING:
    from ..denoise_client import DenoiseInitialSettings


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
        self,
        use_nice: bool,
        shield: str,
        scaling_governor: str,
        no_turbo: Union[bool, str],
        minimize_perf_sampling: Union[bool, str],
    ):
        self.use_nice = use_nice
        self.shield = shield
        self.scaling_governor = scaling_governor
        self.no_turbo = no_turbo
        self.minimize_perf_sampling = minimize_perf_sampling

        self._initial_capabilities = None
        self._possible = None

    def __eq__(self, other):
        if other is None:
            return False

        return (
            self.use_nice == other.use_nice
            and self.shield == other.shield
            and self.scaling_governor == other.scaling_governor
            and self.no_turbo == other.no_turbo
            and self.minimize_perf_sampling == other.minimize_perf_sampling
        )

    @classmethod
    def default(cls):
        return Denoise(True, "basic", "performance", True, True)

    @classmethod
    def system_default(cls):
        """Do not change settings and rely on system defaults."""
        return Denoise(False, "no_change", "no_change", "no_change", "no_change")

    @property
    def requested_nice(self) -> bool:
        return self.use_nice

    @property
    def requested_shield(self) -> bool:
        return self.shield != "no_change"

    @property
    def requested_scaling_governor(self) -> bool:
        return self.scaling_governor != "no_change"

    @property
    def requested_no_turbo(self) -> bool:
        return self.no_turbo != "no_change"

    @property
    def requested_minimize_perf_sampling(self) -> bool:
        return self.minimize_perf_sampling != "no_change"

    def needs_denoise(self) -> bool:
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

    def possible_settings(self, capabilities: "DenoiseInitialSettings"):
        if self._initial_capabilities != capabilities:
            assert self._initial_capabilities is None
            self._initial_capabilities = capabilities
            self._possible = Denoise(
                self.use_nice if capabilities.can_set_nice is True else False,
                self.shield if capabilities.can_set_shield is True else "no_change",
                (
                    self.scaling_governor
                    if capabilities.can_set_scaling_governor is True
                    else "no_change"
                ),
                self.no_turbo if capabilities.can_set_no_turbo is True else "no_change",
                (
                    self.minimize_perf_sampling
                    if capabilities.can_minimize_perf_sampling is True
                    else "no_change"
                ),
            )
        return self._possible

    def restore_initial(self, capabilities: "DenoiseInitialSettings"):
        return Denoise(
            False,
            self.shield if capabilities.can_set_shield is True else "no_change",
            (
                capabilities.initial_scaling_governor
                if capabilities.can_set_scaling_governor is True
                else self.scaling_governor
            ),
            (
                capabilities.initial_no_turbo
                if capabilities.can_set_no_turbo is True
                else self.no_turbo
            ),
            capabilities.can_minimize_perf_sampling is True,
        )

    @classmethod
    def max_union(cls, a, b) -> "Denoise":
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
