"""cocotb tests for models/sram_256x32_1rw1r.sv against spec/sram_spec.md.

Every test compares the RTL to a tiny Python reference model (a dict).
When the real OpenRAM macro or the custom array exists, these same tests
should pass on it too. That's what "meets the spec" means.
"""
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge

WORDS, MASK32 = 256, 0xFFFF_FFFF


async def setup(dut):
    """Start one shared clock (the flagship ties clk0 = clk1) and idle both ports."""
    clk = Clock(dut.clk0, 10, unit="ns")
    cocotb.start_soon(clk.start())
    cocotb.start_soon(Clock(dut.clk1, 10, unit="ns").start())
    dut.csb0.value, dut.web0.value, dut.wmask0.value = 1, 1, 0
    dut.addr0.value, dut.din0.value = 0, 0
    dut.csb1.value, dut.addr1.value = 1, 0
    await FallingEdge(dut.clk0)


async def write(dut, addr, data, mask=0xF):
    dut.csb0.value, dut.web0.value = 0, 0
    dut.addr0.value, dut.din0.value, dut.wmask0.value = addr, data, mask
    await FallingEdge(dut.clk0)
    dut.csb0.value, dut.web0.value = 1, 1


async def read0(dut, addr):
    dut.csb0.value, dut.web0.value, dut.addr0.value = 0, 1, addr
    await FallingEdge(dut.clk0)   # sampled at the rising edge in between
    dut.csb0.value = 1
    return int(dut.dout0.value)


async def read1(dut, addr):
    # Wait on clk0, not clk1: the two clocks are identical, and waiting on a
    # different clock object can resume in the same timestep (before any
    # rising edge), which makes the read look like X.
    dut.csb1.value, dut.addr1.value = 0, addr
    await FallingEdge(dut.clk0)
    dut.csb1.value = 1
    return int(dut.dout1.value)


def apply_mask(old, new, mask):
    out = old
    for b in range(4):
        if mask >> b & 1:
            out = (out & ~(0xFF << 8 * b)) | (new & (0xFF << 8 * b))
    return out & MASK32


@cocotb.test()
async def write_then_read_both_ports(dut):
    """Fill every address, read it back on port 0 and on port 1."""
    await setup(dut)
    ref = {a: random.getrandbits(32) for a in range(WORDS)}
    for a, d in ref.items():
        await write(dut, a, d)
    for a, d in ref.items():
        assert await read0(dut, a) == d, f"port 0 addr {a}"
        assert await read1(dut, a) == d, f"port 1 addr {a}"


@cocotb.test()
async def byte_mask(dut):
    """Only bytes with their wmask0 bit set change."""
    await setup(dut)
    await write(dut, 7, 0x1122_3344)
    await write(dut, 7, 0xAABB_CCDD, mask=0b0101)   # bytes 0 and 2
    assert await read0(dut, 7) == 0x11BB_33DD


@cocotb.test()
async def idle_holds_dout(dut):
    """With chip select high, dout keeps the last value read."""
    await setup(dut)
    await write(dut, 3, 0xDEAD_BEEF)
    assert await read0(dut, 3) == 0xDEAD_BEEF
    await write(dut, 3, 0x0000_0000)   # a write must not change dout0
    for _ in range(5):
        await RisingEdge(dut.clk0)
    assert int(dut.dout0.value) == 0xDEAD_BEEF


@cocotb.test()
async def accumulator_pattern(dut):
    """The flagship's use case: read on port 1, add, write back on port 0, every cycle.

    Different addresses each cycle (the spec says same-address read+write
    in one cycle is undefined, so the test schedules around it like the
    flagship must).
    """
    await setup(dut)
    rows = 16
    ref = [0] * rows
    for r in range(rows):
        await write(dut, r, 0)
    for _ in range(50):
        r = random.randrange(rows)
        inc = random.randrange(1 << 16)
        cur = await read1(dut, r)
        assert cur == ref[r]
        ref[r] = (cur + inc) & MASK32
        await write(dut, r, ref[r])
    for r in range(rows):
        assert await read0(dut, r) == ref[r]


@cocotb.test()
async def random_ops(dut):
    """Random reads/writes/masks on both ports vs. the Python reference."""
    await setup(dut)
    ref = {}
    for a in range(WORDS):
        d = random.getrandbits(32)
        await write(dut, a, d)
        ref[a] = d
    for _ in range(1000):
        a = random.randrange(WORDS)
        op = random.choice(("w", "r0", "r1"))
        if op == "w":
            d, m = random.getrandbits(32), random.randrange(16)
            await write(dut, a, d, m)
            ref[a] = apply_mask(ref[a], d, m)
        elif op == "r0":
            assert await read0(dut, a) == ref[a], f"port 0 addr {a}"
        else:
            assert await read1(dut, a) == ref[a], f"port 1 addr {a}"
