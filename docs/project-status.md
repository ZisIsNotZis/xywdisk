# xywdisk project status

## Classification

Standalone bench scratch: a one-shot script that drives a private thermal plate
(47 Modbus TCP actuator channels + a 34-channel IR sensor socket) and searches
for set-points that null the measured field. Not a library, not a package, no
entrypoint wrapper.

## Status

Archive — abandoned in July 2025, never finished. The acquisition path was run
against real hardware, and four capture files (`real*.47f,34f`, 1987 rows
reserved, 1929 holding data) survive. The control path does not work as
committed: `disk.py` raises at line 107 and then calls `JFit`, a name defined
nowhere in the repo. Kept for reference and as the unedited predecessor of the
published `disk` repo.

## Evidence

- `disk.py` — 108 raw lines as archived (121 after the env-var genericisation);
  connects to `HEAT_HOST` / `PTM_HOST` (Modbus TCP)
  and `SENSOR_HOST:SENSOR_PORT` (raw socket, `b'GetData'` → ASCII CSV);
  `F()` writes registers, settles, averages 10 samples, stores `y - 120.1`.
- `disk.old.py` — the earlier, coherent revision: same I/O, plus an explicit
  finite-difference diffusion solver (`Sim`), sklearn surrogate stacking
  (`Add`, `GPR`) and a `while Y[I-1].std() > …` control loop.
- `control-loop.ipynb` — the interleaved correct version of `F()`
  (`ptm.write_registers(4085, x[7:]*400)`), plus `Jac` and a hand-rolled
  Gauss–Newton / line-search loop.
- `data-inspection.ipynb` — hardware-free data inspection: memmap load,
  least-squares sensitivity `w`, `matplotlib` heatmaps of `log|w|`.
- `real*.47f,34f` — read/write numpy memmaps, `dtype('47f,34f')` =
  `[('f0','<f4',(47,)),('f1','<f4',(34,))]`, 324 B/row; row counts 1081 / 303 /
  93 / 510 (file size ÷ 324). The filename *is* the dtype string.
- Row occupancy, measured on the committed bytes (a row counts when its `f1` is
  not all zero): 1080 / 292 / 48 / 509 of 1081 / 303 / 93 / 510 — 1929 of 1987
  reserved rows. `real2` has zero holes at rows 287, 289, 290; `real3` stops at
  row 48 while holding 70 written set-point vectors, i.e. 22 commands were sent
  whose readings never landed.
- `shape=9999` is dead in all three code paths. `np.memmap(path, '47f,34f',
  shape=9999)` asks for 3.24 MB; the committed files are 30,132–350,244 B, so
  numpy raises `ValueError: mmap length is greater than file size` before the
  first hardware call — `disk.py` line 98, `data-inspection.ipynb` cell 1, and
  `control-loop.ipynb` cell 1. The hardware-free path therefore needs that
  number replaced with the real row count (or the `shape=` argument dropped)
  before it runs at all.
- Lineage: `disk.old.py` diffs against the published `disk`
  (`github.com/ZisIsNotZis/disk`) `disk.py` in only four places (settle test,
  `sleep(4)`, a commented sim line, and `real2.47f,34f` vs `in.ixy`).

## Boundaries

Nothing can be re-executed without the bench: the Modbus devices, the sensor
socket, the pre-allocated memmaps, and the experiment metadata (row ordering,
units, which file is which run) are all absent. The archived `disk.py` has an
undriven second actuator bank (`ptm` receives `x[:7]` instead of `x[7:]`) and an
unreachable optimiser tail, so its published form must not be read as a working
controller. The original private tree had no license; this public archive is
released under AGPL-3.0-only (see `LICENSE`). `disk.py` was exercised once,
manually, by its author; there are no tests.
