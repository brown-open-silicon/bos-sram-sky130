"""cocotb tests for models/ternary_word_check.sv."""
import random

import cocotb
from cocotb.triggers import Timer

LANES = 16


def ref(word):
    lanes = [(word >> 2 * i) & 0b11 for i in range(LANES)]
    invalid = sum((c == 0b11) << i for i, c in enumerate(lanes))
    return invalid, int(invalid != 0), bin(invalid).count("1")


async def check(dut, word):
    dut.word.value = word
    await Timer(1, unit="ns")
    got = (int(dut.invalid.value), int(dut.any_invalid.value), int(dut.n_invalid.value))
    assert got == ref(word), f"word {word:08x}: got {got}, want {ref(word)}"


@cocotb.test()
async def valid_words_pass(dut):
    """Words built only from 00/01/10 never flag."""
    for _ in range(200):
        word = sum(random.choice((0b00, 0b01, 0b10)) << 2 * i for i in range(LANES))
        await check(dut, word)
        assert int(dut.any_invalid.value) == 0


@cocotb.test()
async def single_flip_detected(dut):
    """Flip one bit of a lane holding +1 (01) or -1 (10) and it becomes 11."""
    word = 0x5555_5555            # every lane = 01 (+1)
    for lane in range(LANES):
        flipped = word ^ (1 << (2 * lane + 1))   # 01 -> 11
        await check(dut, flipped)
        assert int(dut.n_invalid.value) == 1


@cocotb.test()
async def corner_cases(dut):
    for word in (0x0000_0000, 0xFFFF_FFFF, 0xAAAA_AAAA, 0x5555_5555):
        await check(dut, word)
    for _ in range(500):
        await check(dut, random.getrandbits(32))
