"""Build + run the cocotb tests with Icarus Verilog.

  python3 tb/run.py           # all
  python3 tb/run.py sram      # one
"""
import sys
from pathlib import Path

from cocotb_tools.runner import get_results, get_runner

ROOT = Path(__file__).resolve().parents[1]

# name -> (sources, toplevel, cocotb test module)
TESTS = {
    "sram":  (["models/sram_256x32_1rw1r.sv"], "sram_256x32_1rw1r", "test_sram"),
    "check": (["models/ternary_word_check.sv"], "ternary_word_check", "test_check"),
}

failed = 0
for name in sys.argv[1:] or TESTS:
    sources, top, module = TESTS[name]
    runner = get_runner("icarus")
    build_dir = ROOT / "build" / "sim" / name
    runner.build(
        sources=[ROOT / s for s in sources],
        hdl_toplevel=top,
        build_dir=build_dir,
        timescale=("1ns", "1ps"),
        always=True,
    )
    results = runner.test(
        hdl_toplevel=top,
        test_module=module,
        test_dir=Path(__file__).parent,
        build_dir=build_dir,
    )
    failed += get_results(results)[1]
sys.exit(1 if failed else 0)
