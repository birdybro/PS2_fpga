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
DSLLV_FUNCTION = 20
DSRLV_FUNCTION = 22
DSRAV_FUNCTION = 23
DSLL_FUNCTION = 56
DSRL_FUNCTION = 58
DSRA_FUNCTION = 59
DSLL32_FUNCTION = 60
DSRL32_FUNCTION = 62
DSRA32_FUNCTION = 63
LUI_OPCODE = 15
ORI_OPCODE = 13
ANDI_OPCODE = 12
XORI_OPCODE = 14
ADDIU_OPCODE = 9
DADDIU_OPCODE = 25
SLTI_OPCODE = 10
SLTIU_OPCODE = 11
ADDU_FUNCTION = 33
DADDU_FUNCTION = 45
DSUBU_FUNCTION = 47
MULT_FUNCTION = 24
MULTU_FUNCTION = 25
DIV_FUNCTION = 26
DIVU_FUNCTION = 27
MFHI_FUNCTION = 16
MTHI_FUNCTION = 17
MFLO_FUNCTION = 18
MTLO_FUNCTION = 19
MMI_OPCODE = 28
MULT1_FUNCTION = 24
MULTU1_FUNCTION = 25
DIV1_FUNCTION = 26
SUBU_FUNCTION = 35
AND_FUNCTION = 36
OR_FUNCTION = 37
XOR_FUNCTION = 38
NOR_FUNCTION = 39
SLT_FUNCTION = 42
SLTU_FUNCTION = 43
SCALAR_WIDTH = 64
WORD_WIDTH = 32
HILO_WIDTH = 64
SCALAR_MASK = (1 << SCALAR_WIDTH) - 1
WORD_MASK = (1 << WORD_WIDTH) - 1
HILO_MASK = (1 << HILO_WIDTH) - 1


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


def encode_dsll(destination: int, source: int, shift_amount: int) -> int:
    """Encode one canonical SPECIAL DSLL word with its reserved field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    sa = _require_shift_amount(shift_amount)
    return (rt << 16) | (rd << 11) | (sa << 6) | DSLL_FUNCTION


def encode_dsrl(destination: int, source: int, shift_amount: int) -> int:
    """Encode one canonical SPECIAL DSRL word with its reserved field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    sa = _require_shift_amount(shift_amount)
    return (rt << 16) | (rd << 11) | (sa << 6) | DSRL_FUNCTION


def encode_dsra(destination: int, source: int, shift_amount: int) -> int:
    """Encode one canonical SPECIAL DSRA word with its reserved field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    sa = _require_shift_amount(shift_amount)
    return (rt << 16) | (rd << 11) | (sa << 6) | DSRA_FUNCTION


def encode_dsll32(destination: int, source: int, shift_amount: int) -> int:
    """Encode canonical SPECIAL DSLL32 with its low five count bits."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    sa = _require_shift_amount(shift_amount)
    return (rt << 16) | (rd << 11) | (sa << 6) | DSLL32_FUNCTION


def encode_dsrl32(destination: int, source: int, shift_amount: int) -> int:
    """Encode canonical SPECIAL DSRL32 with its low five count bits."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    sa = _require_shift_amount(shift_amount)
    return (rt << 16) | (rd << 11) | (sa << 6) | DSRL32_FUNCTION


def encode_dsra32(destination: int, source: int, shift_amount: int) -> int:
    """Encode canonical SPECIAL DSRA32 with its low five count bits."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    sa = _require_shift_amount(shift_amount)
    return (rt << 16) | (rd << 11) | (sa << 6) | DSRA32_FUNCTION


def encode_sllv(destination: int, source: int, shift_register: int) -> int:
    """Encode canonical SPECIAL SLLV with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    rs = _require_gpr_index(shift_register)
    return (rs << 21) | (rt << 16) | (rd << 11) | SLLV_FUNCTION


def encode_dsllv(destination: int, source: int, shift_register: int) -> int:
    """Encode canonical SPECIAL DSLLV with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    rs = _require_gpr_index(shift_register)
    return (rs << 21) | (rt << 16) | (rd << 11) | DSLLV_FUNCTION


def encode_dsrlv(destination: int, source: int, shift_register: int) -> int:
    """Encode canonical SPECIAL DSRLV with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    rs = _require_gpr_index(shift_register)
    return (rs << 21) | (rt << 16) | (rd << 11) | DSRLV_FUNCTION


def encode_dsrav(destination: int, source: int, shift_register: int) -> int:
    """Encode canonical SPECIAL DSRAV with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rt = _require_gpr_index(source)
    rs = _require_gpr_index(shift_register)
    return (rs << 21) | (rt << 16) | (rd << 11) | DSRAV_FUNCTION


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


def encode_xori(destination: int, source: int, immediate: int) -> int:
    """Encode XORI with a zero-extended 16-bit immediate."""
    rt = _require_gpr_index(destination)
    rs = _require_gpr_index(source)
    value = _require_unsigned("immediate", immediate, 0xFFFF)
    return (XORI_OPCODE << 26) | (rs << 21) | (rt << 16) | value


def encode_daddiu(destination: int, source: int, immediate: int) -> int:
    """Encode DADDIU with a sign-extended 16-bit immediate."""
    rt = _require_gpr_index(destination)
    rs = _require_gpr_index(source)
    value = _require_unsigned("immediate", immediate, 0xFFFF)
    return (DADDIU_OPCODE << 26) | (rs << 21) | (rt << 16) | value


def encode_addiu(destination: int, source: int, immediate: int) -> int:
    """Encode ADDIU with its architectural unsigned 16-bit field."""
    rt = _require_gpr_index(destination)
    rs = _require_gpr_index(source)
    value = _require_unsigned("immediate", immediate, 0xFFFF)
    return (ADDIU_OPCODE << 26) | (rs << 21) | (rt << 16) | value


def encode_slti(destination: int, source: int, immediate: int) -> int:
    """Encode SLTI with its architectural unsigned 16-bit field."""
    rt = _require_gpr_index(destination)
    rs = _require_gpr_index(source)
    value = _require_unsigned("immediate", immediate, 0xFFFF)
    return (SLTI_OPCODE << 26) | (rs << 21) | (rt << 16) | value


def encode_sltiu(destination: int, source: int, immediate: int) -> int:
    """Encode SLTIU with its architectural unsigned 16-bit field."""
    rt = _require_gpr_index(destination)
    rs = _require_gpr_index(source)
    value = _require_unsigned("immediate", immediate, 0xFFFF)
    return (SLTIU_OPCODE << 26) | (rs << 21) | (rt << 16) | value


def encode_addu(destination: int, source_a: int, source_b: int) -> int:
    """Encode canonical SPECIAL ADDU with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rs = _require_gpr_index(source_a)
    rt = _require_gpr_index(source_b)
    return (rs << 21) | (rt << 16) | (rd << 11) | ADDU_FUNCTION


def encode_daddu(destination: int, source_a: int, source_b: int) -> int:
    """Encode canonical SPECIAL DADDU with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rs = _require_gpr_index(source_a)
    rt = _require_gpr_index(source_b)
    return (rs << 21) | (rt << 16) | (rd << 11) | DADDU_FUNCTION


def encode_dsubu(destination: int, minuend: int, subtrahend: int) -> int:
    """Encode canonical SPECIAL DSUBU with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rs = _require_gpr_index(minuend)
    rt = _require_gpr_index(subtrahend)
    return (rs << 21) | (rt << 16) | (rd << 11) | DSUBU_FUNCTION


def encode_mult(result_destination: int, source_a: int, source_b: int) -> int:
    """Encode R5900 SPECIAL MULT with its optional rd and reserved sa clear."""
    rd = _require_gpr_index(result_destination)
    rs = _require_gpr_index(source_a)
    rt = _require_gpr_index(source_b)
    return (rs << 21) | (rt << 16) | (rd << 11) | MULT_FUNCTION


def encode_multu(result_destination: int, source_a: int, source_b: int) -> int:
    """Encode R5900 SPECIAL MULTU with its optional rd and reserved sa clear."""
    rd = _require_gpr_index(result_destination)
    rs = _require_gpr_index(source_a)
    rt = _require_gpr_index(source_b)
    return (rs << 21) | (rt << 16) | (rd << 11) | MULTU_FUNCTION


def encode_div(dividend: int, divisor: int) -> int:
    """Encode canonical R5900 SPECIAL DIV with reserved rd and sa clear."""
    rs = _require_gpr_index(dividend)
    rt = _require_gpr_index(divisor)
    return (rs << 21) | (rt << 16) | DIV_FUNCTION


def encode_divu(dividend: int, divisor: int) -> int:
    """Encode canonical R5900 SPECIAL DIVU with reserved rd and sa clear."""
    rs = _require_gpr_index(dividend)
    rt = _require_gpr_index(divisor)
    return (rs << 21) | (rt << 16) | DIVU_FUNCTION


def encode_mfhi(destination: int) -> int:
    """Encode canonical R5900 SPECIAL MFHI with all reserved fields clear."""
    rd = _require_gpr_index(destination)
    return (rd << 11) | MFHI_FUNCTION


def encode_mthi(source: int) -> int:
    """Encode canonical R5900 SPECIAL MTHI with all reserved fields clear."""
    rs = _require_gpr_index(source)
    return (rs << 21) | MTHI_FUNCTION


def encode_mflo(destination: int) -> int:
    """Encode canonical R5900 SPECIAL MFLO with all reserved fields clear."""
    rd = _require_gpr_index(destination)
    return (rd << 11) | MFLO_FUNCTION


def encode_mtlo(source: int) -> int:
    """Encode canonical R5900 SPECIAL MTLO with all reserved fields clear."""
    rs = _require_gpr_index(source)
    return (rs << 21) | MTLO_FUNCTION


def encode_mult1(destination: int, multiplicand: int, multiplier: int) -> int:
    """Encode canonical R5900 MMI MULT1 with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rs = _require_gpr_index(multiplicand)
    rt = _require_gpr_index(multiplier)
    return (MMI_OPCODE << 26) | (rs << 21) | (rt << 16) | (rd << 11) | MULT1_FUNCTION


def encode_multu1(destination: int, multiplicand: int, multiplier: int) -> int:
    """Encode canonical R5900 MMI MULTU1 with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rs = _require_gpr_index(multiplicand)
    rt = _require_gpr_index(multiplier)
    return (MMI_OPCODE << 26) | (rs << 21) | (rt << 16) | (rd << 11) | MULTU1_FUNCTION


def encode_div1(dividend: int, divisor: int) -> int:
    """Encode canonical R5900 MMI DIV1 with reserved rd and sa clear."""
    rs = _require_gpr_index(dividend)
    rt = _require_gpr_index(divisor)
    return (MMI_OPCODE << 26) | (rs << 21) | (rt << 16) | DIV1_FUNCTION


def encode_subu(destination: int, minuend: int, subtrahend: int) -> int:
    """Encode canonical SPECIAL SUBU with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rs = _require_gpr_index(minuend)
    rt = _require_gpr_index(subtrahend)
    return (rs << 21) | (rt << 16) | (rd << 11) | SUBU_FUNCTION


def encode_and(destination: int, source_a: int, source_b: int) -> int:
    """Encode canonical SPECIAL AND with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rs = _require_gpr_index(source_a)
    rt = _require_gpr_index(source_b)
    return (rs << 21) | (rt << 16) | (rd << 11) | AND_FUNCTION


def encode_or(destination: int, source_a: int, source_b: int) -> int:
    """Encode canonical SPECIAL OR with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rs = _require_gpr_index(source_a)
    rt = _require_gpr_index(source_b)
    return (rs << 21) | (rt << 16) | (rd << 11) | OR_FUNCTION


def encode_xor(destination: int, source_a: int, source_b: int) -> int:
    """Encode canonical SPECIAL XOR with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rs = _require_gpr_index(source_a)
    rt = _require_gpr_index(source_b)
    return (rs << 21) | (rt << 16) | (rd << 11) | XOR_FUNCTION


def encode_nor(destination: int, source_a: int, source_b: int) -> int:
    """Encode canonical SPECIAL NOR with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rs = _require_gpr_index(source_a)
    rt = _require_gpr_index(source_b)
    return (rs << 21) | (rt << 16) | (rd << 11) | NOR_FUNCTION


def encode_slt(destination: int, source_a: int, source_b: int) -> int:
    """Encode canonical SPECIAL SLT with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rs = _require_gpr_index(source_a)
    rt = _require_gpr_index(source_b)
    return (rs << 21) | (rt << 16) | (rd << 11) | SLT_FUNCTION


def encode_sltu(destination: int, source_a: int, source_b: int) -> int:
    """Encode canonical SPECIAL SLTU with its reserved shift field clear."""
    rd = _require_gpr_index(destination)
    rs = _require_gpr_index(source_a)
    rt = _require_gpr_index(source_b)
    return (rs << 21) | (rt << 16) | (rd << 11) | SLTU_FUNCTION


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


def _as_signed_scalar(value: int) -> int:
    """Interpret an already width-masked scalar as a signed Python integer."""
    scalar = value & SCALAR_MASK
    return scalar - (1 << SCALAR_WIDTH) if scalar & (1 << (SCALAR_WIDTH - 1)) else scalar


@dataclass(frozen=True, slots=True)
class R5900State:
    """Hold immutable timing-free state for future instruction transitions."""

    gprs: tuple[int, ...] = field(default_factory=_zero_gprs)
    pc: int = 0
    hi: int = 0
    lo: int = 0
    hi1: int = 0
    lo1: int = 0

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
        for name, value in (
            ("HI", self.hi),
            ("LO", self.lo),
            ("HI1", self.hi1),
            ("LO1", self.lo1),
        ):
            _require_unsigned(name, value, HILO_MASK)

    @classmethod
    def initial(
        cls,
        *,
        start_pc: int = 0,
        hi: int = 0,
        lo: int = 0,
        hi1: int = 0,
        lo1: int = 0,
    ) -> R5900State:
        """Create explicitly selected deterministic simulation state."""
        return cls(
            pc=_require_unsigned("start PC", start_pc, PC_MASK),
            hi=_require_unsigned("initial HI", hi, HILO_MASK),
            lo=_require_unsigned("initial LO", lo, HILO_MASK),
            hi1=_require_unsigned("initial HI1", hi1, HILO_MASK),
            lo1=_require_unsigned("initial LO1", lo1, HILO_MASK),
        )

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

    def write_hi(self, value: int) -> R5900State:
        """Return a snapshot with a normalized computed primary HI value."""
        normalized = _require_integer("HI result", value) & HILO_MASK
        return self if self.hi == normalized else replace(self, hi=normalized)

    def write_lo(self, value: int) -> R5900State:
        """Return a snapshot with a normalized computed primary LO value."""
        normalized = _require_integer("LO result", value) & HILO_MASK
        return self if self.lo == normalized else replace(self, lo=normalized)

    def write_hi1(self, value: int) -> R5900State:
        """Return a snapshot with a normalized computed secondary HI1 value."""
        normalized = _require_integer("HI1 result", value) & HILO_MASK
        return self if self.hi1 == normalized else replace(self, hi1=normalized)

    def write_lo1(self, value: int) -> R5900State:
        """Return a snapshot with a normalized computed secondary LO1 value."""
        normalized = _require_integer("LO1 result", value) & HILO_MASK
        return self if self.lo1 == normalized else replace(self, lo1=normalized)

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

    def _step_immediate_doubleword_shift(self, word: int, function: int) -> R5900State:
        """Apply one admitted low-range constant doubleword shift."""
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        shift_amount = (word >> 6) & 0x1F
        if function in (DSLL32_FUNCTION, DSRL32_FUNCTION, DSRA32_FUNCTION):
            shift_amount += 32
        source_scalar = self.read_gpr(rt) & SCALAR_MASK
        if function in (DSLL_FUNCTION, DSLL32_FUNCTION):
            shifted_scalar = source_scalar << shift_amount
        elif function in (DSRL_FUNCTION, DSRL32_FUNCTION):
            shifted_scalar = source_scalar >> shift_amount
        else:
            shifted_scalar = _as_signed_scalar(source_scalar) >> shift_amount
        result = _merge_scalar(self.read_gpr(rd), shifted_scalar)
        return self.write_gpr(rd, result)

    def _step_variable_shift(self, word: int, function: int) -> R5900State:
        """Apply one admitted register-count word shift without advancing PC."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        if function in (DSLLV_FUNCTION, DSRLV_FUNCTION, DSRAV_FUNCTION):
            shift_amount = self.read_gpr(rs) & 0x3F
            source_scalar = self.read_gpr(rt) & SCALAR_MASK
            if function == DSLLV_FUNCTION:
                shifted_scalar = source_scalar << shift_amount
            elif function == DSRLV_FUNCTION:
                shifted_scalar = source_scalar >> shift_amount
            else:
                shifted_scalar = _as_signed_scalar(source_scalar) >> shift_amount
            result = _merge_scalar(self.read_gpr(rd), shifted_scalar)
            return self.write_gpr(rd, result)
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

    def _step_xori(self, word: int) -> R5900State:
        """XOR one source scalar lane with a zero-extended immediate."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        scalar = (self.read_gpr(rs) & SCALAR_MASK) ^ (word & 0xFFFF)
        result = _merge_scalar(self.read_gpr(rt), scalar)
        return self.write_gpr(rt, result)

    def _step_addiu(self, word: int) -> R5900State:
        """Add one signed immediate modulo 32 bits without an overflow exception."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        immediate = word & 0xFFFF
        if immediate & 0x8000:
            immediate -= 1 << 16
        result_word = (self.read_gpr(rs) & WORD_MASK) + immediate
        result = _merge_scalar_word(self.read_gpr(rt), result_word)
        return self.write_gpr(rt, result)

    def _step_daddiu(self, word: int) -> R5900State:
        """Add one signed immediate modulo 64 bits without an overflow exception."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        immediate = word & 0xFFFF
        if immediate & 0x8000:
            immediate -= 1 << 16
        result_scalar = (self.read_gpr(rs) & SCALAR_MASK) + immediate
        result = _merge_scalar(self.read_gpr(rt), result_scalar)
        return self.write_gpr(rt, result)

    def _step_slti(self, word: int) -> R5900State:
        """Compare a signed scalar source against a sign-extended immediate."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        immediate = word & 0xFFFF
        if immediate & 0x8000:
            immediate -= 1 << 16
        result = _merge_scalar(
            self.read_gpr(rt),
            int(_as_signed_scalar(self.read_gpr(rs)) < immediate),
        )
        return self.write_gpr(rt, result)

    def _step_sltiu(self, word: int) -> R5900State:
        """Compare an unsigned scalar source against a sign-extended immediate."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        immediate = word & 0xFFFF
        if immediate & 0x8000:
            immediate |= SCALAR_MASK ^ 0xFFFF
        result = _merge_scalar(
            self.read_gpr(rt),
            int((self.read_gpr(rs) & SCALAR_MASK) < immediate),
        )
        return self.write_gpr(rt, result)

    def _step_signed_immediate_group(self, word: int, opcode: int) -> R5900State:
        """Dispatch one operation whose 16-bit immediate is sign-extended."""
        if opcode == ADDIU_OPCODE:
            return self._step_addiu(word)
        if opcode == DADDIU_OPCODE:
            return self._step_daddiu(word)
        if opcode == SLTI_OPCODE:
            return self._step_slti(word)
        return self._step_sltiu(word)

    def _step_addu(self, word: int) -> R5900State:
        """Add two source words modulo 32 bits without an overflow exception."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        result_word = (self.read_gpr(rs) & WORD_MASK) + (self.read_gpr(rt) & WORD_MASK)
        result = _merge_scalar_word(self.read_gpr(rd), result_word)
        return self.write_gpr(rd, result)

    def _step_daddu(self, word: int) -> R5900State:
        """Add two source scalars modulo 64 bits without an overflow exception."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        result_scalar = (self.read_gpr(rs) & SCALAR_MASK) + (self.read_gpr(rt) & SCALAR_MASK)
        result = _merge_scalar(self.read_gpr(rd), result_scalar)
        return self.write_gpr(rd, result)

    def _step_dsubu(self, word: int) -> R5900State:
        """Subtract source scalars modulo 64 bits without an overflow exception."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        result_scalar = (self.read_gpr(rs) & SCALAR_MASK) - (self.read_gpr(rt) & SCALAR_MASK)
        result = _merge_scalar(self.read_gpr(rd), result_scalar)
        return self.write_gpr(rd, result)

    def _step_mult(self, word: int) -> R5900State:
        """Multiply signed source words into sign-extended primary HI and LO halves."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        product = _as_signed_word(self.read_gpr(rs)) * _as_signed_word(self.read_gpr(rt))
        product_bits = product & HILO_MASK
        lo = _as_signed_word(product_bits) & SCALAR_MASK
        hi = _as_signed_word(product_bits >> WORD_WIDTH) & SCALAR_MASK
        updated = self.write_hi(hi).write_lo(lo)
        if rd != 0:
            updated = updated.write_gpr(rd, _merge_scalar(self.read_gpr(rd), lo))
        return updated

    def _step_multu(self, word: int) -> R5900State:
        """Multiply unsigned source words into sign-extended primary HI and LO halves."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        product = (self.read_gpr(rs) & WORD_MASK) * (self.read_gpr(rt) & WORD_MASK)
        lo = _as_signed_word(product) & SCALAR_MASK
        hi = _as_signed_word(product >> WORD_WIDTH) & SCALAR_MASK
        updated = self.write_hi(hi).write_lo(lo)
        if rd != 0:
            updated = updated.write_gpr(rd, _merge_scalar(self.read_gpr(rd), lo))
        return updated

    def _step_mult1(self, word: int) -> R5900State:
        """Multiply signed source words into secondary HI1 and LO1."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        product = _as_signed_word(self.read_gpr(rs)) * _as_signed_word(self.read_gpr(rt))
        lo1 = _as_signed_word(product) & SCALAR_MASK
        hi1 = _as_signed_word(product >> WORD_WIDTH) & SCALAR_MASK
        updated = self.write_hi1(hi1).write_lo1(lo1)
        if rd != 0:
            updated = updated.write_gpr(rd, _merge_scalar(self.read_gpr(rd), lo1))
        return updated

    def _step_multu1(self, word: int) -> R5900State:
        """Multiply unsigned source words into secondary HI1 and LO1."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        product = (self.read_gpr(rs) & WORD_MASK) * (self.read_gpr(rt) & WORD_MASK)
        lo1 = _as_signed_word(product) & SCALAR_MASK
        hi1 = _as_signed_word(product >> WORD_WIDTH) & SCALAR_MASK
        updated = self.write_hi1(hi1).write_lo1(lo1)
        if rd != 0:
            updated = updated.write_gpr(rd, _merge_scalar(self.read_gpr(rd), lo1))
        return updated

    def _step_div(self, word: int) -> R5900State:
        """Divide signed source words into primary LO quotient and HI remainder."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        dividend = _as_signed_word(self.read_gpr(rs))
        divisor = _as_signed_word(self.read_gpr(rt))
        if dividend == -(1 << 31) and divisor == -1:
            quotient, remainder = dividend, 0
        elif divisor == 0:
            quotient, remainder = (1 if dividend < 0 else -1), dividend
        else:
            magnitude = abs(dividend) // abs(divisor)
            quotient = -magnitude if (dividend < 0) != (divisor < 0) else magnitude
            remainder = dividend - quotient * divisor
        return self.write_hi(remainder & SCALAR_MASK).write_lo(quotient & SCALAR_MASK)

    def _step_div1(self, word: int) -> R5900State:
        """Divide signed source words into secondary LO1 quotient and HI1 remainder."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        dividend = _as_signed_word(self.read_gpr(rs))
        divisor = _as_signed_word(self.read_gpr(rt))
        if dividend == -(1 << 31) and divisor == -1:
            quotient, remainder = dividend, 0
        elif divisor == 0:
            quotient, remainder = (1 if dividend < 0 else -1), dividend
        else:
            magnitude = abs(dividend) // abs(divisor)
            quotient = -magnitude if (dividend < 0) != (divisor < 0) else magnitude
            remainder = dividend - quotient * divisor
        return self.write_hi1(remainder & SCALAR_MASK).write_lo1(quotient & SCALAR_MASK)

    def _step_divu(self, word: int) -> R5900State:
        """Divide unsigned source words into sign-extended primary HI and LO."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        dividend = self.read_gpr(rs) & WORD_MASK
        divisor = self.read_gpr(rt) & WORD_MASK
        if divisor == 0:
            quotient, remainder = WORD_MASK, dividend
        else:
            quotient, remainder = divmod(dividend, divisor)
        hi = _as_signed_word(remainder) & SCALAR_MASK
        lo = _as_signed_word(quotient) & SCALAR_MASK
        return self.write_hi(hi).write_lo(lo)

    def _step_mfhi(self, word: int) -> R5900State:
        """Copy the complete primary HI scalar into one GPR low lane."""
        rd = (word >> 11) & 0x1F
        return self.write_gpr(rd, _merge_scalar(self.read_gpr(rd), self.hi))

    def _step_mflo(self, word: int) -> R5900State:
        """Copy the complete primary LO scalar into one GPR low lane."""
        rd = (word >> 11) & 0x1F
        return self.write_gpr(rd, _merge_scalar(self.read_gpr(rd), self.lo))

    def _step_mthi(self, word: int) -> R5900State:
        """Copy one GPR's low scalar lane into primary HI."""
        rs = (word >> 21) & 0x1F
        return self.write_hi(self.read_gpr(rs) & SCALAR_MASK)

    def _step_mtlo(self, word: int) -> R5900State:
        """Copy one GPR's low scalar lane into primary LO."""
        rs = (word >> 21) & 0x1F
        return self.write_lo(self.read_gpr(rs) & SCALAR_MASK)

    def _step_primary_hilo_transfer(self, word: int, function: int) -> R5900State:
        """Dispatch one admitted primary HI/LO transfer operation."""
        if function == MFHI_FUNCTION:
            return self._step_mfhi(word)
        if function == MFLO_FUNCTION:
            return self._step_mflo(word)
        if function == MTHI_FUNCTION:
            return self._step_mthi(word)
        return self._step_mtlo(word)

    def _step_register_or_multiply(self, word: int, function: int) -> R5900State:
        """Dispatch the admitted SPECIAL register and primary multiply group."""
        if function == MULT_FUNCTION:
            return self._step_mult(word)
        if function == MULTU_FUNCTION:
            return self._step_multu(word)
        return self._step_register_alu(word, function)

    def _step_subu(self, word: int) -> R5900State:
        """Subtract source words modulo 32 bits without an overflow exception."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        result_word = (self.read_gpr(rs) & WORD_MASK) - (self.read_gpr(rt) & WORD_MASK)
        result = _merge_scalar_word(self.read_gpr(rd), result_word)
        return self.write_gpr(rd, result)

    def _step_and(self, word: int) -> R5900State:
        """AND the low 64-bit scalar lanes and preserve the destination upper lane."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        result = _merge_scalar(self.read_gpr(rd), self.read_gpr(rs) & self.read_gpr(rt))
        return self.write_gpr(rd, result)

    def _step_or(self, word: int) -> R5900State:
        """OR the low 64-bit scalar lanes and preserve the destination upper lane."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        result = _merge_scalar(self.read_gpr(rd), self.read_gpr(rs) | self.read_gpr(rt))
        return self.write_gpr(rd, result)

    def _step_xor(self, word: int) -> R5900State:
        """XOR the low 64-bit scalar lanes and preserve the destination upper lane."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        result = _merge_scalar(self.read_gpr(rd), self.read_gpr(rs) ^ self.read_gpr(rt))
        return self.write_gpr(rd, result)

    def _step_nor(self, word: int) -> R5900State:
        """NOR the low 64-bit scalar lanes and preserve the destination upper lane."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        scalar = ~(self.read_gpr(rs) | self.read_gpr(rt)) & SCALAR_MASK
        result = _merge_scalar(self.read_gpr(rd), scalar)
        return self.write_gpr(rd, result)

    def _step_slt(self, word: int) -> R5900State:
        """Compare signed low 64-bit scalar lanes and preserve the destination upper lane."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        result = _merge_scalar(
            self.read_gpr(rd),
            int(_as_signed_scalar(self.read_gpr(rs)) < _as_signed_scalar(self.read_gpr(rt))),
        )
        return self.write_gpr(rd, result)

    def _step_sltu(self, word: int) -> R5900State:
        """Compare unsigned low 64-bit scalar lanes and preserve the destination upper lane."""
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        result = _merge_scalar(
            self.read_gpr(rd),
            int((self.read_gpr(rs) & SCALAR_MASK) < (self.read_gpr(rt) & SCALAR_MASK)),
        )
        return self.write_gpr(rd, result)

    def _step_logical_or_compare(self, word: int, function: int) -> R5900State:
        """Dispatch one admitted SPECIAL logical or comparison operation."""
        if function == AND_FUNCTION:
            return self._step_and(word)
        if function == OR_FUNCTION:
            return self._step_or(word)
        if function == XOR_FUNCTION:
            return self._step_xor(word)
        if function == NOR_FUNCTION:
            return self._step_nor(word)
        if function == SLT_FUNCTION:
            return self._step_slt(word)
        return self._step_sltu(word)

    def _step_register_alu(self, word: int, function: int) -> R5900State:
        """Dispatch one admitted SPECIAL register ALU operation."""
        if function == ADDU_FUNCTION:
            return self._step_addu(word)
        if function == DADDU_FUNCTION:
            return self._step_daddu(word)
        if function == SUBU_FUNCTION:
            return self._step_subu(word)
        if function == DSUBU_FUNCTION:
            return self._step_dsubu(word)
        return self._step_logical_or_compare(word, function)

    def _step_special(self, word: int) -> R5900State:
        """Validate and execute one supported nonzero SPECIAL instruction."""
        reserved_rs = (word >> 21) & 0x1F
        reserved_shift = (word >> 6) & 0x1F
        function = word & 0x3F
        immediate = reserved_rs == 0
        variable = reserved_shift == 0
        if (word & 0x0000_FFC0) == 0 and function in (DIV_FUNCTION, DIVU_FUNCTION):
            return self._step_div(word) if function == DIV_FUNCTION else self._step_divu(word)
        read_hilo = (word & 0x03FF_07C0) == 0 and function in (
            MFHI_FUNCTION,
            MFLO_FUNCTION,
        )
        write_hilo = (word & 0x001F_FFC0) == 0 and function in (
            MTHI_FUNCTION,
            MTLO_FUNCTION,
        )
        if read_hilo or write_hilo:
            return self._step_primary_hilo_transfer(word, function)
        if variable and function in (
            MULT_FUNCTION,
            MULTU_FUNCTION,
            ADDU_FUNCTION,
            DADDU_FUNCTION,
            SUBU_FUNCTION,
            DSUBU_FUNCTION,
            AND_FUNCTION,
            OR_FUNCTION,
            XOR_FUNCTION,
            NOR_FUNCTION,
            SLT_FUNCTION,
            SLTU_FUNCTION,
        ):
            return self._step_register_or_multiply(word, function)
        if immediate and function in (
            DSLL_FUNCTION,
            DSRL_FUNCTION,
            DSRA_FUNCTION,
            DSLL32_FUNCTION,
            DSRL32_FUNCTION,
            DSRA32_FUNCTION,
        ):
            return self._step_immediate_doubleword_shift(word, function)
        if immediate and function in (SLL_FUNCTION, SRL_FUNCTION, SRA_FUNCTION):
            return self._step_immediate_shift(word, function)
        if variable and function in (
            SLLV_FUNCTION,
            SRLV_FUNCTION,
            SRAV_FUNCTION,
            DSLLV_FUNCTION,
            DSRLV_FUNCTION,
            DSRAV_FUNCTION,
        ):
            return self._step_variable_shift(word, function)
        msg = f"unsupported R5900 instruction: 0x{word:08x}"
        raise UnsupportedInstructionError(msg)

    def _step_mmi(self, word: int) -> R5900State:
        """Validate and execute one supported MMI primary function."""
        function = word & 0x3F
        if (word & 0x7C0) == 0:
            if function == MULT1_FUNCTION:
                return self._step_mult1(word)
            if function == MULTU1_FUNCTION:
                return self._step_multu1(word)
        if (word & 0xFFC0) == 0 and function == DIV1_FUNCTION:
            return self._step_div1(word)
        msg = f"unsupported R5900 instruction: 0x{word:08x}"
        raise UnsupportedInstructionError(msg)

    def step(self, instruction: int) -> R5900State:
        """Execute one supported instruction and return its architectural successor."""
        word = _require_unsigned("instruction", instruction, INSTRUCTION_MASK)
        if word == NOP_INSTRUCTION:
            updated = self
        else:
            opcode = word >> 26
            reserved_rs = (word >> 21) & 0x1F
            if opcode in (ADDIU_OPCODE, DADDIU_OPCODE, SLTI_OPCODE, SLTIU_OPCODE):
                updated = self._step_signed_immediate_group(word, opcode)
            elif opcode == SPECIAL_OPCODE:
                updated = self._step_special(word)
            elif opcode == MMI_OPCODE:
                updated = self._step_mmi(word)
            elif opcode == ANDI_OPCODE:
                updated = self._step_andi(word)
            elif opcode == XORI_OPCODE:
                updated = self._step_xori(word)
            elif opcode == ORI_OPCODE:
                updated = self._step_ori(word)
            elif opcode == LUI_OPCODE and reserved_rs == 0:
                updated = self._step_lui(word)
            else:
                msg = f"unsupported R5900 instruction: 0x{word:08x}"
                raise UnsupportedInstructionError(msg)
        return updated.write_pc(self.pc + 4)
