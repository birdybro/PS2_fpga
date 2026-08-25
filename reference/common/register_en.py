"""Correctness-oriented model of the common enabled register."""

from dataclasses import dataclass, field


@dataclass
class RegisterEnModel:
    """Model synchronous reset, enabled load, and disabled hold behavior."""

    width: int = 32
    reset_value: int = 0
    value: int = field(init=False)

    def __post_init__(self) -> None:
        if self.width <= 0:
            msg = "register width must be positive"
            raise ValueError(msg)
        self.mask = (1 << self.width) - 1
        self.value = self.reset_value & self.mask

    def tick(self, *, reset_n: bool, enable: bool, data: int) -> int:
        """Advance one rising edge and return the newly visible value."""
        if not reset_n:
            self.value = self.reset_value & self.mask
        elif enable:
            self.value = data & self.mask
        return self.value
