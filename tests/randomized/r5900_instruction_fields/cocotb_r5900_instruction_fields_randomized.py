"""Deterministic randomized verification for R5900 instruction-field extraction."""

import os
import random

import cocotb
from cocotb.triggers import Timer

RANDOM_CASES = 1024


def expected_fields(word: int) -> tuple[int, ...]:
    """Return all expected fields using Python masks and arithmetic shifts."""
    immediate = word & 0xFFFF
    sign_extended = immediate - 0x1_0000 if immediate & 0x8000 else immediate
    return (
        (word >> 26) & 0x3F,
        (word >> 21) & 0x1F,
        (word >> 16) & 0x1F,
        (word >> 11) & 0x1F,
        (word >> 6) & 0x1F,
        word & 0x3F,
        immediate,
        sign_extended & 0xFFFF_FFFF,
        immediate,
        word & 0x03FF_FFFF,
    )


@cocotb.test()
async def test_r5900_instruction_fields_randomized(dut) -> None:
    """Compare every output over reproducible boundary-heavy random words."""
    seed = int(os.environ.get("RANDOM_SEED", "1"))
    generator = random.Random(seed)
    signals = (
        dut.opcode_o,
        dut.rs_o,
        dut.rt_o,
        dut.rd_o,
        dut.shift_amount_o,
        dut.function_o,
        dut.immediate_o,
        dut.immediate_sign_extended_o,
        dut.immediate_zero_extended_o,
        dut.target_o,
    )
    boundary_words = (
        0,
        1,
        0x7FFF,
        0x8000,
        0xFFFF,
        0x7FFF_FFFF,
        0x8000_0000,
        0xFFFF_FFFF,
        0xAAAA_AAAA,
        0x5555_5555,
    )
    words = (*boundary_words, *(generator.getrandbits(32) for _ in range(RANDOM_CASES)))

    for iteration, word in enumerate(words):
        dut.instruction_i.value = word
        await Timer(1, unit="ns")
        actual = tuple(int(signal.value) for signal in signals)
        expected = expected_fields(word)
        assert actual == expected, (
            f"seed={seed} iteration={iteration} word=0x{word:08x} "
            f"expected={expected} actual={actual}"
        )
