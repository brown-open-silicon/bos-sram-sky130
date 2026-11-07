# SRAM interface spec (v0.1)

This is the contract between the SRAM team and the flagship accelerator.
If you change anything here (ports, widths, timing), bump the version,
note it in the changelog at the bottom, and tell the flagship leads first.

## Summary

| Item | Value |
|---|---|
| Process | SkyWater SKY130 (`sky130A`), 1.8 V core |
| Capacity | 1 KB = 256 words × 32 bits |
| Ports | Port 0: read/write (1RW). Port 1: read-only (1R) |
| Write granularity | Byte mask (`wmask0[3:0]`, one bit per 8-bit byte) |
| Clocking | Synchronous. Inputs sampled on the rising edge |
| Read latency | 1 cycle: address sampled on edge N, data valid before edge N+1 |
| Baseline macro | OpenRAM `sky130_sram_1kbyte_1rw1r_32x256_8` (same ports) |

Why this shape:
- It matches OpenRAM's silicon-proven SKY130 configuration, so there is
  always a working fallback with the exact same pins.
- The flagship accumulator does read-modify-write every cycle, so it needs
  a second port (read on port 1, write on port 0).
- A 32-bit word holds 4 INT8 weights or 16 ternary weights, so the same
  memory serves both phases of the flagship.

## Ports

Names follow OpenRAM so the behavioral model and the real macro are drop-in swaps.
`csb` and `web` are **active low**.

| Port | Dir | Width | Meaning |
|---|---|---|---|
| `clk0` | in | 1 | Port 0 clock |
| `csb0` | in | 1 | Port 0 chip select (0 = active) |
| `web0` | in | 1 | Port 0 write enable (0 = write, 1 = read) |
| `wmask0` | in | 4 | Byte write mask, bit *i* enables `din0[8i+7:8i]` |
| `addr0` | in | 8 | Port 0 address |
| `din0` | in | 32 | Write data |
| `dout0` | out | 32 | Port 0 read data |
| `clk1` | in | 1 | Port 1 clock |
| `csb1` | in | 1 | Port 1 chip select (0 = active) |
| `addr1` | in | 8 | Port 1 address |
| `dout1` | out | 32 | Port 1 read data |
| `vccd1`, `vssd1` | inout | 1 | Power, only when `USE_POWER_PINS` is defined |

In the flagship, tie `clk0` and `clk1` to the same clock.

## Behavior

1. **Read (port 0 or 1):** chip select low (and `web0 = 1` on port 0) at rising edge N →
   `dout` holds `mem[addr]` from shortly after edge N until the next read on that port.
2. **Write (port 0):** `csb0 = 0`, `web0 = 0` at rising edge N → every byte with its
   `wmask0` bit set is written. Unmasked bytes keep their old value.
3. **Idle:** chip select high → `dout` holds its last value.
4. **Write and read the same address in the same cycle** (port 0 writes, port 1 reads):
   **undefined.** The behavioral model returns the old data, but the real macro may not.
   The flagship must not depend on this. Schedule around it.
5. **Power-up contents:** undefined. Initialize before use.

## Word layout

INT8 weights (4 per word), little-endian bytes:

```
bit:  31      24 23      16 15       8 7        0
      [ weight 3 ][ weight 2 ][ weight 1 ][ weight 0 ]   (signed two's complement)
```

Ternary weights (16 per word, 2 bits each), lane *i* at bits `[2i+1:2i]`:

| Code | Value |
|---|---|
| `00` | 0 |
| `01` | +1 |
| `10` | −1 |
| `11` | **invalid** (a stored bit flipped) |

This matches the flagship's `pe_ternary` / `array_ternary` encoding.
`models/ternary_word_check.sv` flags invalid codes as words come out of the SRAM.

## Phase 2: monitor hooks (reserved, not in v0.1)

These are planned for the custom instrumented array. Until they exist,
the flagship should not connect anything to them.

| Hook | Purpose |
|---|---|
| Separate array supply | Sweep voltage for data-retention and bit-error tests |
| Leakage-timer column + counter | Temperature sensing from bitline leakage |
| Replica read-path column | Timing-margin tracking vs. temperature and process |
| BIST start / done / error count | Built-in self-test: write a pattern, read back, count errors |

All of these will come out as digital values readable over the chip's Wishbone registers.

## Changelog

- v0.1 (2026-11-07): first version. 256×32, 1RW+1R, byte mask, 1-cycle read.
