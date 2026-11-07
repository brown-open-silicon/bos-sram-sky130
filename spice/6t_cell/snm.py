"""Read static noise margin (SNM) from the butterfly sweeps in build/spice/.

For each temperature: take the half-cell curve y = f(x), mirror it (x = f(y)),
and find the largest square that fits inside each lobe. SNM = the smaller one.

Uses the standard 45-degree rotation trick: in coordinates u = (x - y)/sqrt2,
v = (x + y)/sqrt2, each lobe's largest square has side = max gap between the
two curves along v, divided by sqrt2.

  python3 spice/6t_cell/snm.py
"""
from pathlib import Path

import numpy as np

S2 = np.sqrt(2)


def load(path):
    d = np.loadtxt(path)
    return d[:, 0], d[:, 1]          # x = v(qb_in), y = v(q)


def snm(x, y):
    # curve A: y = f(x). curve B: mirror, points (f(x), x).
    ua, va = (x - y) / S2, (x + y) / S2
    ub, vb = (y - x) / S2, (y + x) / S2
    order = np.argsort(ub)
    ub, vb = ub[order], vb[order]
    u = np.linspace(max(ua.min(), ub.min()), min(ua.max(), ub.max()), 2000)
    order = np.argsort(ua)
    gap = np.interp(u, ua[order], va[order]) - np.interp(u, ub, vb)
    lobe1 = gap[u < 0]
    lobe2 = gap[u > 0]
    side = lambda g: np.abs(g).max() / S2 if len(g) else 0.0
    return min(side(lobe1), side(lobe2))


def main():
    files = sorted(Path("build/spice").glob("butterfly_*C.txt"),
                   key=lambda f: int(f.stem.split("_")[1].rstrip("C")))
    if not files:
        print("no sweeps found: run `make spice` first")
        return
    print("temp    read SNM")
    for f in files:
        t = f.stem.split("_")[1]
        print(f"{t:>6}  {snm(*load(f)) * 1000:7.1f} mV")


if __name__ == "__main__":
    main()
