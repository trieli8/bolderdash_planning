# BoulderDash – Planning-Driven Stones & Gems

This repository combines:
- **Stones & Gems** (BoulderDash-like game engine + GUI)
- **Forced-Action FF** planner
- **Fast Downward** planner
- **Python wrapper tools** that provide a clean, unified interface to planners and GUI


---

## Repository Layout

```
boulderdash/
├── Makefile                     # top-level build (game + planners)
├── stonesandgem/                # Stones & Gems (CMake project, submodule)
│   └── build/
│       └── bin/
│           └── gui              # GUI executable
├── planners/
│   ├── forced-action-ff/        # Forced-Action FF planner (submodule)
│   │   └── ff                   # FF binary
│   └── fast-downward/           # Fast Downward planner (submodule)
│       └── fast-downward.py
├── tools/                       # Python wrappers (stable interface)
│   ├── common.py
│   ├── plan.py                  # planner runner
│   └── gui.py                   # GUI launcher
├── pddl/                        # domains, problems, levels
├── plans/                       # generated plans (auto-created)
└── README.md
```

---

## Prerequisites

- macOS or Linux
- Python 3.9+
- CMake
- GNU Make
- C/C++ compiler (clang or gcc)

---

## Clone the Repository

This repo uses **git submodules**.

```bash
git clone --recurse-submodules https://github.com/<you>/boulderdash.git
cd boulderdash
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

---

## Build Everything

From the repo root:

```bash
make
```

This will:

1. Build **Forced-Action FF**
2. Build **Fast Downward**
3. Build **Stones & Gems** using CMake

### Clean build artefacts

```bash
make clean
```

### Full reset (including Fast Downward builds)

```bash
make distclean
```

---

## Python Wrapper Tools (Recommended Interface)

All interaction with planners and GUI should go through **`tools/`**.
This keeps planner quirks out of your game and experiments.

---

## Run the GUI

The GUI binary lives at:

```
./stonesandgem/build/bin/gui
```

Use the wrapper instead:

```bash
python tools/gui.py
```

Run with a specific level (optional):

```bash
python tools/gui.py --level pddl/levels/level01.txt
```

---

## Generate Plans (FF / Fast Downward)

Use **`tools/plan.py`** — this is the canonical planner interface.

### Default (auto planner, outputs BOTH formats)

```bash
python tools/plan.py \
  --domain pddl/domain.pddl \
  --problem pddl/p01.pddl
```

This will:

- Try **Forced-Action FF**, then **Fast Downward** if FF fails
- Write outputs to:

```
plans/p01/
├── plan.txt        # plain text (one action per line)
├── plan.json       # structured JSON
├── raw_stdout.log
└── raw_stderr.log
```

---

### Force a specific planner

```bash
# Forced-Action FF
python tools/plan.py --planner ff --domain ... --problem ...

# Fast Downward
python tools/plan.py --planner fd --domain ... --problem ...
```

### Change Fast Downward alias

```bash
python tools/plan.py \
  --planner fd \
  --fd-alias seq-sat-lama-2011 \
  --domain pddl/domain.pddl \
  --problem pddl/p01.pddl
```

---

## Plan Output Formats

### `plan.txt` (human-readable)

```
(move agent c1 c2)
(push agent stone c3 c4)
...
```

### `plan.json` (machine-friendly, GUI-ready)

```json
{
  "planner": "ff",
  "domain": "pddl/domain.pddl",
  "problem": "pddl/p01.pddl",
  "status": "solved",
  "actions": [
    { "name": "move", "args": ["agent", "c1", "c2"] },
    { "name": "push", "args": ["agent", "stone", "c3", "c4"] }
  ],
  "metrics": {
    "returncode": 0,
    "time_sec": 0.41
  }
}
```

---


## Typical Workflow

```bash
make
python tools/plan.py --domain pddl/domain.pddl --problem pddl/p01.pddl
python tools/gui.py --level pddl/levels/level01.txt
```

---

## Level
0  → Agent
1  → Empty
2  → Dirt
3  → Stone
5  → Gem
7  → Brick (wall / solid)