"""Timing-free architectural state for the Emotion Engine R5900 core."""

from dataclasses import dataclass, field, replace

GPR_COUNT = 32
GPR_WIDTH = 128
PC_WIDTH = 32
INSTRUCTION_WIDTH = 32
GPR_MASK = (1 << GPR_WIDTH) - 1
PC_MASK = (1 << PC_WIDTH) - 1
INSTRUCTION_MASK = (1 << INSTRUCTION_WIDTH) - 1
NOP_INSTRUCTION = 0


class UnsupportedInstructionError(ValueError):
    """Report an instruction absent from the timing-free functional model."""


def _zero_gprs() -> tuple[int, ...]:
    """Return a fresh immutable architectural reset register tuple."""
    return (0,) * GPR_COUNT


def _require_integer(name: str, value: object) -> int:
    """Reject booleans and non-integers at an architectural state boundary."""
    if type(value) is not int:
        msg = f"{name} must be an integer"
        raise TypeError(msg)
    return value


def _require_unsigned(name: str, value: object, mask: int) -> int:
    """Validate an already-normalized unsigned architectural value."""
    integer = _require_integer(name, value)
    if not 0 <= integer <= mask:
        msg = f"{name} is outside its architectural width: {integer}"
        raise ValueError(msg)
    return integer


def _require_gpr_index(index: object) -> int:
    """Validate a five-bit architectural GPR index without coercion."""
    integer = _require_integer("GPR index", index)
    if not 0 <= integer < GPR_COUNT:
        msg = f"GPR index out of range: {integer}"
        raise IndexError(msg)
    return integer


@dataclass(frozen=True, slots=True)
class R5900State:
    """Hold immutable timing-free state for future instruction transitions."""

    gprs: tuple[int, ...] = field(default_factory=_zero_gprs)
    pc: int = 0

    def __post_init__(self) -> None:
        """Reject malformed snapshots instead of silently repairing model state."""
        if not isinstance(self.gprs, tuple):
            msg = "GPR state must be an immutable tuple"
            raise TypeError(msg)
        if len(self.gprs) != GPR_COUNT:
            msg = f"GPR state must contain exactly {GPR_COUNT} values"
            raise ValueError(msg)
        for index, value in enumerate(self.gprs):
            _require_unsigned(f"GPR {index}", value, GPR_MASK)
        if self.gprs[0] != 0:
            msg = "GPR 0 must remain zero"
            raise ValueError(msg)
        _require_unsigned("PC", self.pc, PC_MASK)

    @classmethod
    def initial(cls, *, start_pc: int = 0) -> R5900State:
        """Create zeroed GPR state at an externally selected simulation entry point."""
        return cls(pc=_require_unsigned("start PC", start_pc, PC_MASK))

    def read_gpr(self, index: int) -> int:
        """Read one validated 128-bit GPR value."""
        return self.gprs[_require_gpr_index(index)]

    def write_gpr(self, index: int, value: int) -> R5900State:
        """Return a snapshot with one explicitly width-normalized GPR result."""
        destination = _require_gpr_index(index)
        normalized = _require_integer("GPR result", value) & GPR_MASK
        if destination == 0 or self.gprs[destination] == normalized:
            return self
        updated = list(self.gprs)
        updated[destination] = normalized
        return replace(self, gprs=tuple(updated))

    def write_pc(self, value: int) -> R5900State:
        """Return a snapshot with a width-normalized computed PC value."""
        normalized = _require_integer("PC result", value) & PC_MASK
        if self.pc == normalized:
            return self
        return replace(self, pc=normalized)

    def step(self, instruction: int) -> R5900State:
        """Execute one supported instruction and return its architectural successor."""
        word = _require_unsigned("instruction", instruction, INSTRUCTION_MASK)
        if word != NOP_INSTRUCTION:
            msg = f"unsupported R5900 instruction: 0x{word:08x}"
            raise UnsupportedInstructionError(msg)
        return self.write_pc(self.pc + 4)
