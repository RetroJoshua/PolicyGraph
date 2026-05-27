# DGL Version Compatibility

This document explains which DGL (Deep Graph Library) versions PolicyGraph
supports, why, and how to install the correct one.

## Available DGL Versions

The DGL project ships pre-built wheels from
[https://data.dgl.ai/wheels/repo.html](https://data.dgl.ai/wheels/repo.html).
At the time of writing the available releases include:

- `1.0.2`
- `1.1.0`, `1.1.1`, `1.1.2` ✅ (PolicyGraph uses **1.1.2**)
- `2.0.0`, `2.0.0+cu118`, `2.0.0+cu121` ❌
- `2.2.1`, `2.2.1+cu118`, `2.2.1+cu121` ❌

> ⚠️ **`dgl==1.1.3` does NOT exist.** Older PolicyGraph instructions
> referenced `1.1.3` by mistake. If you see a `No matching distribution
> found for dgl==1.1.3` error, that is why. Use `1.1.2` instead.

## Why 1.1.2?

- **Latest stable 1.1.x release** — most polished bug-fix release in the
  1.1 series.
- **No `graphbolt` dependency.** DGL 2.x introduced a hard dependency on
  `graphbolt`, which has its own build/runtime issues on Windows and
  Python 3.11. PolicyGraph does not need the 2.x feature set, so we stay
  on 1.1.x to keep installs reliable.
- **Works with PyTorch 2.0+.** Compatible with the `torch>=2.0.0`
  declared in `setup.py` / `requirements.txt`.
- **Compatible with Python 3.9, 3.10, and 3.11.** DGL 1.1.x does not
  publish wheels for Python 3.12+, which is also why PolicyGraph’s
  `setup.py` rejects 3.12+.

## Canonical Version Spec

PolicyGraph declares DGL as:

```
dgl>=1.1.0,<1.2.0
```

That range resolves to `1.1.2` today (the highest 1.1.x available) and
will continue to work if a future `1.1.3` is ever published — but it
will **not** silently jump to 2.x.

## Installation

DGL wheels are not on PyPI for every platform, so always include the
DGL wheel index when installing directly.

### Windows (CPU)

```cmd
pip install dgl==1.1.2 -f https://data.dgl.ai/wheels/repo.html
```

### Linux / Mac (CPU)

```bash
pip install dgl==1.1.2 -f https://data.dgl.ai/wheels/repo.html
```

### Range form (equivalent, future-proof within 1.1.x)

```bash
pip install 'dgl>=1.1.0,<1.2.0' -f https://data.dgl.ai/wheels/repo.html
```

### GPU (CUDA 11.8) — optional

```bash
pip install dgl-cu118==1.1.2 -f https://data.dgl.ai/wheels/repo.html
```

## Verifying Your Install

```bash
python -c "import dgl; print('DGL version:', dgl.__version__)"
```

Expected output:

```
DGL version: 1.1.2
```

`setup.py` also prints a warning during install if it detects a DGL
version outside the 1.1.x range.

## Python Version

PolicyGraph supports **Python 3.9, 3.10, or 3.11** (DGL 1.1.x does not
publish wheels for 3.12+). `setup.py` will hard-fail on unsupported
interpreters with a clear message.
