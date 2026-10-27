English | [简体中文](README.zh-CN.md)

<p align="center">
  <img src="assets/logo.svg" alt="xywdisk logo" width="112" height="112">
</p>

<h1 align="center">xywdisk</h1>

<p align="center"><strong>47 actuators in, 34 IR sensors out: a field record of thermal calibration on a heated wafer.</strong></p>

<p align="center"><em>1,987 real plant transitions, the Jacobian search that used them, and an honest account of what never worked.</em></p>

> **Status: archive.** This is the public record of a private bench experiment from June 2025. The acquisition path ran against real hardware; the control path is unfinished. Nothing here can be re-run without the bench, and nothing here is a maintained package.

At a glance:

- **47 → 34 MIMO bench** — 47 Modbus set-points (7 on one PLC, 40 on another) drive a heated plate; a 34-channel IR socket reads the field.
- **1,987 captured rows** in four numpy memmaps: real inputs, real measurements, no simulation.
- **Two notebooks and two script revisions** — the working acquisition code, an earlier surrogate-model controller, and the later model-free search that was never completed.

## Quick start

The only hardware-free path is the data-inspection notebook. It reads one of the committed capture files and plots least-squares sensitivities.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install numpy matplotlib scikit-learn jupyter
jupyter nbconvert --to notebook --execute data-inspection.ipynb
```

The archived acquisition scripts need the bench and are **not runnable end to end**:

```bash
pip install numpy scipy pymodbus

export HEAT_HOST=localhost   HEAT_PORT=502
export PTM_HOST=localhost    PTM_PORT=502
export SENSOR_HOST=localhost SENSOR_PORT=9090
export DISK_DATA=real4.47f,34f

python disk.py   # stops at the bare `raise` described below
```

No endpoint ever defaults to the original private bench; all addresses come from the environment.

## What it can do now

**Working, exercised against hardware**

- Open two Modbus TCP connections and one raw TCP sensor socket.
- Write a 47-value set-point vector with per-bank scaling (`heat` ×100, `ptm` ×400).
- Request `b'GetData'`, parse the ASCII CSV reply, wait for the last 10 samples to settle, and average them.
- Subtract the fixed `120.1` baseline and append a `(47 inputs, 34 outputs)` row to the memmap.
- Inspect the captures offline: load the dtype, fit a linear sensitivity matrix, and visualise it as heatmaps.

**Broken or incomplete, as committed**

- `disk.py` halts at an unconditional `raise` before its optimisation loop. The code below it is unreachable.
- The unreachable tail calls `JFit`, a name defined nowhere in the repository — a `NameError` even if the `raise` is removed.
- `disk.py` writes `x[:7]` to the second PLC instead of `x[7:]`, so 40 of the 47 channels are never driven. `control-loop.ipynb` contains the correct split; this is a regression in the later script.
- `disk.old.py` has a coherent control loop, but its imports and surrogate models only ran with the bench attached.
- There are no tests, no timestamps, and no record of which capture file belongs to which experiment.

## Architecture

```text
        Modbus TCP: 7 set-points        Modbus TCP: 40 set-points
                 │                                │
                 ▼                                ▼
          heat PLC                           ptm PLC
                 └──────────────┬─────────────────┘
                                ▼
                       heated plate / wafer
                                │
                     34-channel IR sensor socket
                                │
                                ▼
              disk.py · disk.old.py · control-loop.ipynb
                                │
                                ▼
                  real*.47f,34f  (numpy memmaps)
                                │
                                ▼
                    data-inspection.ipynb
```

| Component | Role |
| --- | --- |
| `disk.py` | Later, model-free revision: acquisition plus an intended Gauss–Newton / trust-region search. |
| `disk.old.py` | Earlier revision: acquisition, a finite-difference diffusion twin, sklearn surrogates, and a working control loop. |
| `control-loop.ipynb` | The interleaved correct `F()` and the hand-rolled Jacobian / line-search loop. |
| `data-inspection.ipynb` | Hardware-free analysis of the captures: memmap load, sensitivity matrix, heatmaps. |
| `real*.47f,34f` | Raw numpy memmaps — the filename *is* the dtype string. |
| `docs/project-status.md` | The condensed evidence and boundary record. |

## The capture files

Each row stores one acquisition: `f0` is the 47-element set-point vector, `f1` is the 34 sensor means after baseline subtraction. The dtype is `[('f0', '<f4', (47,)), ('f1', '<f4', (34,))]`, 324 bytes per row. `shape=9999` in the code is only a generous upper bound.

| File | Bytes | Rows |
| --- | ---: | ---: |
| `real.47f,34f` | 350,244 | 1,081 |
| `real2.47f,34f` | 98,172 | 303 |
| `real3.47f,34f` | 30,132 | 93 |
| `real4.47f,34f` | 165,240 | 510 |

The files are pre-allocated and partially written; later rows may still be zeros. Units, row ordering, and run identities were never recorded.

## Repository layout

```text
.
├── README.md
├── README.zh-CN.md
├── LICENSE
├── disk.py
├── disk.old.py
├── control-loop.ipynb
├── data-inspection.ipynb
├── real.47f,34f
├── real2.47f,34f
├── real3.47f,34f
├── real4.47f,34f
├── assets/
│   └── logo.svg
└── docs/
    └── project-status.md
```

## How to develop

There is no build, package, test suite, or CI. The repository is a fixed archive, not a starter project.

- Keep the captures byte-for-byte identical.
- Record new findings in `docs/project-status.md`, with the evidence beside the claim.
- Treat the scripts as historical artifacts. If you clean them up, keep the broken revision next to the working one so the lineage stays visible.
- Do not add a bench address, credential, or private network detail to the tree.

## How to contribute

Corrections with evidence are welcome — especially experiment metadata, the meaning of each capture file, or the sensor's physical unit.

- Open an issue with the file, line, or byte offset that supports the correction.
- Keep pull requests narrow: documentation, sanitisation, or a clearly labelled experimental branch.
- Do not present the archived controller as a working system.

## Roadmap

**Implemented**

- [x] Hardware acquisition: Modbus writes, `GetData` reads, settle-and-average, memmap append.
- [x] Four real capture files, 1,987 rows total.
- [x] Offline sensitivity analysis and heatmap inspection.
- [x] Environment-variable sanitisation of every private bench address.
- [x] AGPL-3.0-only licensing and a documented evidence record.

**Planned**

- [ ] Recover experiment metadata: row order, units, and which file is which run.
- [ ] Repair the `disk.py` tail and replace the undefined `JFit` call.
- [ ] Reconcile the `x[:7]` / `x[7:]` actuator-bank regression.
- [ ] Build an offline replay harness so the data can be studied without the bench.

These are possible directions, not promises; no maintainer is actively working on them.

## Future vision

The captures are the part worth keeping. A small replay harness could turn them into a testbed for system identification, sparse Jacobian estimation, and safe set-point search — all without touching the original hardware. The ideal outcome is not a revived bench script, but a clean, honest dataset and a reference controller that others can compare against the later [`disk`](https://github.com/ZisIsNotZis/disk) project.

## Lineage

This repository is the earlier, raw predecessor of the author's published `disk` project. `disk.old.py` is a near-identical ancestor of that repository's `disk.py`; this snapshot additionally preserves the capture data and the unfinished later revision. The name `xywdisk` is the migration label of the original private archive, not the published `disk` repository.

## License

[AGPL-3.0-only](LICENSE). The original private tree had no license; this public archive is released under the GNU Affero General Public License v3.0.
