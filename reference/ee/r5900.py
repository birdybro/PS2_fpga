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
SPECIAL_OPCODE = 0
SLL_FUNCTION = 0
SRL_FUNCTION = 2
SRA_FUNCTION = 3
SLLV_FUNCTION = 4
SRLV_FUNCTION = 6
SRAV_FUNCTION = 7
LUI_OPCODE = 15
ORI_OPCODE = 13
ANDI_OPCODE = 12
SCALAR_WIDTH = 64
WORD_WIDTH = 32
SCALAR_MASK = (1 << SCALAR_WIDTH) - 1
WORD_MASK = (1 << WORD_WIDTH) - 1


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


def _require_shift_amount(shift_amount: object) -> int:
    """Validate the five-bit immediate shift field without masking mistakes."""
    integer = _require_integer("shift amount", shift_amount)
    if not 0 <= integer < WORD_WIDTH:
        msg = f"shift amount out of range: {integer}"
        raise ValueError(msg)
    return integer


def encode_sll(destination: int, source: int, shift_amount: int) -> int:
    """Encode one canonical SPECIAL SLL word with its reserved field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    sa = _require_shift_amount(shift_amount)
    return (rt << 16) | (rd << 11) | (sa << 6)


def encode_srl(destination: int, source: int, shift_amount: int) -> int:
    """Encode one canonical SPECIAL SRL word with its reserved field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    sa = _require_shift_amount(shift_amount)
    return (rt << 16) | (rd << 11) | (sa << 6) | SRL_FUNCTION


def encode_sra(destination: int, source: int, shift_amount: int) -> int:
    """Encode one canonical SPECIAL SRA word with its reserved field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    sa = _require_shift_amount(shift_amount)
    return (rt << 16) | (rd << 11) | (sa << 6) | SRA_FUNCTION


def encode_sllv(destination: int, source: int, shift_register: int) -> int:
    """Encode canonical SPECIAL SLLV with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    rs = _require_gpr_index(shift_register)
    return (rs << 21) | (rt << 16) | (rd << 11) | SLLV_FUNCTION


def encode_srlv(destination: int, source: int, shift_register: int) -> int:
    """Encode canonical SPECIAL SRLV with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    rs = _require_gpr_index(shift_register)
    return (rs << 21) | (rt << 16) | (rd << 11) | SRLV_FUNCTION


def encode_srav(destination: int, source: int, shift_register: int) -> int:
    """Encode canonical SPECIAL SRAV with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    rs = _require_gpr_index(shift_register)
    return (rs << 21) | (rt << 16) | (rd << 11) | SRAV_FUNCTION


def encode_lui(destination: int, immediate: int) -> int:
    """Encode canonical LUI with its reserved source field clear."""
    rt = _require_gpr_index(destination)
    value = _require_unsigned("immediate", immediate, 0xFFFF)
    return (LUI_OPCODE << 26) | (rt << 16) | value


def encode_ori(destination: int, source: int, immediate: int) -> int:
    """Encode ORI with a zero-extended 16-bit immediate."""
    rt = _require_gpr_index(destination)
    rs = _require_gpr_index(source)
    value = _require_unsigned("immediate", immediate, 0xFFFF)
    return (ORI_OPCODE << 26) | (rs << 21) | (rt << 16) | value


def encode_andi(destination: int, source: int, immediate: int) -> int:
    """Encode ANDI with a zero-extended 16-bit immediate."""
    rt = _require_gpr_index(destination)
    rs = _require_gpr_index(source)
    value = _require_unsigned("immediate", immediate, 0xFFFF)
    return (ANDI_OPCODE << 26) | (rs << 21) | (rt << 16) | value


def _merge_scalar(old_destination: int, scalar: int) -> int:
    """Replace the low 64-bit scalar lane and preserve the upper GPR lane."""
    return (old_destination & (GPR_MASK ^ SCALAR_MASK)) | (scalar & SCALAR_MASK)


def _merge_scalar_word(old_destination: int, word: int) -> int:
    """Sign-extend one word through the scalar lane and preserve the upper lane."""
    normalized_word = word & WORD_MASK
    scalar_result = normalized_word
    if normalized_word & (1 << (WORD_WIDTH - 1)):
        scalar_result |= SCALAR_MASK ^ WORD_MASK
    return _merge_scalar(old_destination, scalar_result)


def _as_signed_word(value: int) -> int:
    """Interpret an already width-masked word as a signed Python integer."""
    word = value & WORD_MASK
    return word - (1 << WORD_WIDTH) if word & (1 << (WORD_WIDTH - 1)) else word


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

    def _step_immediate_shift(self, word: int, function: int) -> R5900State:
        """Apply one admitted constant word shift without advancing PC."""
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        shift_amount = (word >> 6) & 0x1F
        source_word = self.read_gpr(rt) & WORD_MASK
        if function == SLL_FUNCTION:
            shifted_word = source_word << shift_amount
        elif function == SRL_FUNCTION:
            shifted_word = source_word >> shift_amount
        else:
            shifted_word = _as_signed_word(source_word) >> shift_amount
        result = _merge_scalar_word(self.read_gpr(rd), shifted_word)
        return self.write_gpr(rd, result)

    def _step_variable_shift(self, word: int, function: int) -> R5900State:
        """Apply one admitted register-count word shift without advancing PC."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        shift_amount = self.read_gpr(rs) & 0x1F
        source_word = self.read_gpr(rt) & WORD_MASK
        if function == SLLV_FUNCTION:
            shifted_word = source_word << shift_amount
        elif function == SRLV_FUNCTION:
            shifted_word = source_word >> shift_amount
        else:
            shifted_word = _as_signed_word(source_word) >> shift_amount
        result = _merge_scalar_word(self.read_gpr(rd), shifted_word)
        return self.write_gpr(rd, result)

    def _step_lui(self, word: int) -> R5900State:
        """Form one sign-extended upper-immediate word without advancing PC."""
        rt = (word >> 16) & 0x1F
        result = _merge_scalar_word(self.read_gpr(rt), (word & 0xFFFF) << 16)
        return self.write_gpr(rt, result)

    def _step_ori(self, word: int) -> R5900State:
        """OR a zero-extended immediate into one source scalar lane."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        scalar = (self.read_gpr(rs) & SCALAR_MASK) | (word & 0xFFFF)
        result = _merge_scalar(self.read_gpr(rt), scalar)
        return self.write_gpr(rt, result)

    def _step_andi(self, word: int) -> R5900State:
        """AND one source scalar lane with a zero-extended immediate."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        scalar = (self.read_gpr(rs) & SCALAR_MASK) & (word & 0xFFFF)
        result = _merge_scalar(self.read_gpr(rt), scalar)
        return self.write_gpr(rt, result)

    def step(self, instruction: int) -> R5900State:
        """Execute one supported instruction and return its architectural successor."""
        word = _require_unsigned("instruction", instruction, INSTRUCTION_MASK)
        if word == NOP_INSTRUCTION:
            updated = self
        else:
            opcode = word >> 26
            reserved_rs = (word >> 21) & 0x1F
            reserved_shift = (word >> 6) & 0x1F
            function = word & 0x3F
            immediate = opcode == SPECIAL_OPCODE and reserved_rs == 0
            variable = opcode == SPECIAL_OPCODE and reserved_shift == 0
            if opcode == ANDI_OPCODE:
                updated = self._step_andi(word)
            elif opcode == ORI_OPCODE:
                updated = self._step_ori(word)
            elif opcode == LUI_OPCODE and reserved_rs == 0:
                updated = self._step_lui(word)
            elif immediate and function in (SLL_FUNCTION, SRL_FUNCTION, SRA_FUNCTION):
                updated = self._step_immediate_shift(word, function)
            elif variable and function in (SLLV_FUNCTION, SRLV_FUNCTION, SRAV_FUNCTION):
                updated = self._step_variable_shift(word, function)
            else:
                msg = f"unsupported R5900 instruction: 0x{word:08x}"
                raise UnsupportedInstructionError(msg)
        return updated.write_pc(self.pc + 4)
