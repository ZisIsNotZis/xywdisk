# xywdisk

**Status: archive — unreproducible bench scratch, kept for reference.**

A ~June 2025 scratch script that drove a private thermal test bench (47 Modbus
actuator channels + a 34-channel IR sensor socket) and tried to steer the
measured 2-D field towards a target; it exists only as a record of the bench
experiments and cannot be re-run without that hardware.

> The name is the migration label for the private archive directory
> `~/my/xywdisk`. It is **not** the published [`disk`](https://github.com/ZisIsNotZis/disk)
> repo — see [Relationship](#relationship-to-the-published-disk-repo) below.

## What it is

`disk.py` is a one-shot, top-level script (plus its earlier revision
`disk.old.py`) that:

1. opens three network endpoints — two Modbus TCP devices (`heat`, `ptm`) and a
   raw TCP sensor socket;
2. writes a 47-element set-point vector to those devices;
3. polls the sensor socket (ASCII CSV, `b'GetData'` request) until the last 10
   samples are stable (`.max() <= 0.02`), averages them, and stores the 34
   channel means minus a fixed `120.1` baseline;
4. repeats this to fill an on-disk dataset, then attempts a model-free
   Gauss–Newton / trust-region search over the 47 set-points to drive the stored
   measurement vector to zero.

The problem it solved (for one person, one time): closing a slow, noisy,
47-input → 34-output control loop on a heated plate without any plant model,
by logging real transitions and fitting local Jacobians (`Jac`, `Line`, `Jit`,
`root`).

## Device / protocol

Inferred from the code, not from documentation (none survives):

| Endpoint | Protocol | What the code does |
| --- | --- | --- |
| `heat` | Modbus TCP | `write_register(801, 12000)` (enable / power), then `write_registers(5, …)` with the first 7 set-points × 100 |
| `ptm` | Modbus TCP | `write_registers(4085, …)` with the remaining 40 set-points × 400, then `write_register(4211, 65535)` |
| `sensr` | raw TCP | `send(b'GetData')`, `recv(999)` → ASCII CSV; the last 34 fields are taken as the measurement vector |

So the actuator vector is split **7 channels on `heat` + 40 channels on `ptm` =
47**, and the sensor returns **34** channels whose raw magnitude is ~`120.1`
(the code subtracts that scalar before storing). Notebook `Untitled1.ipynb`
cell 1 indirectly labels the split (`print('disk', f0[:7]*100)` and
`print('ptm', f0[7:]*400)`), and the
sensor values look like a temperature in °C — but that last point is inference,
not documentation.

## How to run

There is **no runnable entrypoint on a machine without the bench**. Dependencies
are `numpy`, `scipy` and `pymodbus` (plus `scikit-learn` for the unused helpers
in `disk.old.py`); there is no `requirements.txt` because the original tree had
none.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install numpy scipy pymodbus scikit-learn

# All endpoints were hard-coded to a private bench LAN; point them at yours:
export HEAT_HOST=<redacted:device-host>  HEAT_PORT=502
export PTM_HOST=<redacted:device-host>   PTM_PORT=502
export SENSOR_HOST=<redacted:device-host> SENSOR_PORT=9090
export DISK_DATA=real4.47f,34f           # numpy memmap to open (disk.py)

python disk.py
```

**It still will not complete.** `disk.py` ends its data-collection phase with an
unconditional `raise` (line 107) and the code after it is dead — see
[Implemented vs not](#implemented-vs-not).

The only self-contained parts are the notebook data-inspection cells in
`Untitled1.ipynb` (memmap + matplotlib, no hardware):

```bash
jupyter nbconvert --to notebook --execute Untitled1.ipynb
```

### Genericisation applied during migration

The original files contained real, private bench addresses. They were replaced
with environment lookups so the archive can be published without leaking the
network topology (defaults are `localhost`; no default points at real
hardware):

- `disk.py`, `disk.old.py`, `Untitled.ipynb`: `ModbusTcpClient('<REDACTED:device-host>')`
  → `ModbusTcpClient(os.getenv("HEAT_HOST", "localhost"), port=int(os.getenv("HEAT_PORT", "502")))`,
  and the analogous `PTM_*` and `SENSOR_*` variables for the second PLC and the
  `create_connection` sensor socket (port was hard-coded `9090`).
- The memmap filename was also parameterised: `np.memmap('real4.47f,34f', …)` →
  `np.memmap(os.getenv("DISK_DATA", "real4.47f,34f"), …)` (`disk.old.py` keeps
  its historical default `real2.47f,34f`).
- No credentials, API keys or passwords existed anywhere in the archive — the
  gate below confirms none were introduced.

## Implemented vs not

- **Implemented (and exercised against real hardware):** the acquisition path —
  Modbus register writes, the `GetData`/CSV sensor read, the per-sample settle
  wait, and appending rows to the `real*.47f,34f` memmaps.
- **Not implemented / not working:**
  - `disk.py` aborts before its optimisation loop: bare `raise` at line 107,
    then line 111 calls **`JFit`, which is defined nowhere in the repo**
    (`NameError` even if the `raise` is removed). Everything after line 107 is
    dead code.
  - `disk.py` writes the same first seven values to `ptm`
    (`ptm.write_registers(4085, (x[:7]*400)…` at line 22). The sibling code in
    `Untitled.ipynb` and the scaling intent (`heat` ×100, `ptm` ×400) show this
    should be `x[7:]`; as committed, channels 7–46 of the `ptm` device are never
    driven. This is a regression introduced in `disk.py` versus
    `Untitled.ipynb` cell 1.
  - `disk.old.py` has no such crash but its `while Y[I-1].std() > …` loop also
    only ever ran with the bench attached; the surrogate models it imports
    (sklearn / GPR) appear in commented-out code only.
- **What it does to the device is therefore mixed:** the device-access layer
  really does actuate hardware (it is not read-only), but the search loop that
  was supposed to use the measurements is broken/unreachable. Nothing here was
  ever packaged, tested, or run unattended.

### `disk.py` vs `disk.old.py`

`disk.old.py` (29 May 2025) is the earlier, surrogate-model version: it defines
`Sim` (an explicit finite-difference diffusion-decay solver used as a plant
twin), `Add`/`GPR` model stacking, `fit`/`fitb_1`/`poly`/`hot`, and a working
`while Y[I-1].std() > …` control loop over `real2.47f,34f`. `disk.py` (3 Jun
2025) throws all of that away, adds the model-free `Jac`/`Line`/`Jit`/`root`
Gauss–Newton search, switches the dataset to `real4.47f,34f`, changes the
baseline offset `120` → `120.1`, changes the scale factor to 100/400 for the
two devices (intended per-device resolution), and replaces the std-based settle
test with a consecutive-sample `eps` test — but ships the broken tail described
above. In short: `disk.old.py` is the coherent one; `disk.py` is a later,
incomplete rewrite.

## The data files

`real.47f,34f`, `real2.47f,34f`, `real3.47f,34f`, `real4.47f,34f` are **raw
numpy `memmap` dumps**, not renamed text. The filename is literally the numpy
`dtype` string used to open them: `np.memmap('real4.47f,34f', '47f,34f', shape=9999)`.

Layout, verified by reading the files with `numpy.dtype('47f,34f')`:

- `dtype` = `[('f0', '<f4', (47,)), ('f1', '<f4', (34,))]`, itemsize **324 B**
  (47 × float32 followed by 34 × float32).
- Row = one acquisition: `f0` = the 47-element set-point / actuator vector that
  was written to the bench; `f1` = the 34 sensor channel means after the
  `-120.1` baseline subtraction.
- Actual row counts (the `shape=9999` in code is just a generous upper bound,
  i.e. the files are treated as a growing log):

  | File | Bytes | Rows |
  | --- | ---: | ---: |
  | `real.47f,34f` | 350 244 | 1081 |
  | `real2.47f,34f` | 98 172 | 303 |
  | `real3.47f,34f` | 30 132 | 93 |
  | `real4.47f,34f` | 165 240 | 510 |

What is **unclear**: whether the rows are chronological, which experiment each
file corresponds to, and why four files exist. `disk.py` reads `real4` (510
rows) but drives 47 warm-up writes — it would need at least 47 `I`+47 rows,
which is consistent with 510 but not proof. The code treats `Y.any(1)` as a
"has this row been filled yet" marker, so files are pre-allocated and partially
written; later rows may be zeros. No units, timestamps or metadata were ever
recorded.

## Relationship to the published `disk` repo

The author's published `disk` repo
(`github.com/ZisIsNotZis/disk`) is a **later, sanitised migration of the same
bench work**, and this directory is an earlier snapshot of it. Evidence, not
guesswork:

- The `disk` README describes the identical setup: "steering a physical 2-D
  heated plate (47 Modbus set-points, 34 IR sensor channels)" with
  `scipy.optimize` and sklearn/PyTorch surrogates.
- `disk.old.py` here is the near-identical ancestor of the `disk` repo's
  `disk.py`. Diffing the two checkouts, the imports (`nnls`, sklearn
  `LinearRegression`/`MLPRegressor`/`GPR`/`KNeighborsRegressor`), the `Sim`
  diffusion solver, the `Add`/`GPR` classes and the control loop are unchanged;
  the only differences are the `F()` settle test (`t`/`eps`-based here vs a
  5-consecutive-sample test there), a `sleep(4)` warm-up, a commented-out
  simulated-`Y` line, and the data source (`real2.47f,34f` here vs an `in.ixy`
  dump there — the addresses are already `<REDACTED:…>` placeholders in that
  repo).
- `disk` was migrated in Sep 2025 from the private `~/my` archive; this
  directory (Jun 2025) predates it, keeps raw `Untitled*.ipynb` names, and
  carries the capture data (`real*.47f,34f`) that the published `disk` repo does
  not ship.

The relationship is therefore *predecessor snapshot of the same experiments* —
not a port, fork, or separate project. No code in this directory references the
`disk` repo.

## Status

**Archive / abandoned.** Drafted May–Jun 2025, never finished (`disk.py` raises
before its control loop and references a non-existent `JFit`). Unreproducible
rather than outdated: the stack (numpy/scipy/pymodbus) is still current, but the
hardware, network and experiment metadata are absent, so nothing here can be
re-executed meaningfully. Kept for reference and for the honest record of the
bench work.

## License

**None.** The original tree contained no `LICENSE`, no copyright header and no
`pyproject.toml`/`setup.py`; no license is attached here either, so the code
defaults to all-rights-reserved. Add a license before reuse. The
`Untitled*.ipynb` notebooks are equally unlicensed.
