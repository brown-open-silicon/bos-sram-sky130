# bos-sram-sky130

Brown Open Silicon's on-chip SRAM for SKY130. Built and measured on the
1-year on-chip monitor chip, then reused as the memory in the flagship
accelerator.

**Target:** 1 KB (256 × 32), 1 read/write port + 1 read port, byte mask,
1-cycle read. Full contract: [`spec/sram_spec.md`](spec/sram_spec.md).

## How the pieces fit

```
spec/sram_spec.md ──── the contract (flagship + SRAM team both follow it)
        │
        ├── models/sram_256x32_1rw1r.sv   fake SRAM, usable by the flagship today
        │          │
        │          └── replaced later by ──▶ OpenRAM macro (baseline, fallback)
        │                                     └─▶ custom instrumented array (phase 2)
        │
        └── tb/test_sram.py   the same tests must pass on every version
```

Every version has the same ports, so the flagship never rewires anything.

## Setup (new members)

1. Install Docker Desktop and pull `hpretl/iic-osic-tools:chipathon26` (about 20 GB free disk needed).
2. Clone this repo into your designs folder (`C:\Users\<you>\eda\designs` on Windows, `~/eda/designs` on Mac). Inside the container it is `/foss/designs/bos-sram-sky130`.
3. Copy `setup/designinit` to `eda/designs/.designinit` (one level above this repo) so the container starts on sky130A. Restart the container.
4. Check: `echo $PDK` prints `sky130A`, and `python3 tb/run.py` passes 8 tests.
5. First Xschem example: `cd /foss/designs/bos-sram-sky130/xschem/inverter && xschem TB_inv1.sch`, then Netlist and Simulate. sky130 model loading takes 2 to 5 minutes per simulation.

## Quick start

Needs Docker with `hpretl/iic-osic-tools` (SKY130 PDK, iverilog, cocotb, ngspice, OpenRAM).

```
make pdk-check   # is sky130A installed?
make sim         # RTL tests (8 tests, a few seconds)
make snm         # 6T cell butterfly curves + read SNM at -40/27/100 C
make openram     # generate the baseline macro (slow)
```

No Docker? `make sim-local` works with `iverilog` and `pip install cocotb`.

## Layout

| Path | What |
|---|---|
| `spec/sram_spec.md` | Ports, timing, word layout (INT8 + ternary), phase-2 monitor hooks |
| `models/sram_256x32_1rw1r.sv` | Behavioral SRAM, OpenRAM-compatible port names |
| `models/ternary_word_check.sv` | Flags invalid ternary codes (`11`) on read-out: a free bit-flip monitor |
| `tb/` | cocotb tests: read/write, byte mask, idle, accumulator pattern, 1000 random ops |
| `openram/config_256x32_1rw1r.py` | OpenRAM config for the baseline macro |
| `spice/6t_cell/` | Starter ngspice deck: one 6T cell, read butterfly vs temperature |
| `scripts/eda.sh` | Runs any command in the EDA container with `PDK=sky130A` |
| `setup/designinit` | Copy to `eda/designs/.designinit` to make sky130A the container default |
| `xschem/inverter/` | sky130 inverter + testbench: the first Xschem exercise |

## Using it in the flagship

Add this repo as a submodule and compile `models/sram_256x32_1rw1r.sv`
with your RTL:

```
git submodule add https://github.com/brown-open-silicon/bos-sram-sky130 third_party/bos-sram-sky130
```

Tie `clk0` and `clk1` to the same clock. For the accumulator, read the
running sum on port 1 and write it back on port 0. Don't read and write the
same address in the same cycle (undefined in the spec).

## Roadmap

1. ✅ Spec v0.1, behavioral model, tests
2. Learn: simulate the 6T cell, plot butterfly curves and SNM vs temperature
3. Baseline: generate or pull the OpenRAM macro, run `tb/` against its Verilog model
4. Custom array (~16×16 to 32×32 bits) with monitor hooks: leakage timer,
   replica column, separate array supply, BIST
5. Layout, DRC/LVS clean, onto the on-chip monitor tapeout
6. Measure silicon, write Liberty/LEF, hand to the flagship
