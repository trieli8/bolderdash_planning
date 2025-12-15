# BoulderDash – Planning-Driven Stones & Gems

This repository combines:
- **Stones & Gems** (BoulderDash-like game engine + GUI)
- **Forced-Action FF** planner
- **Fast Downward** planner
- **Python wrapper tools** providing a unified interface to planners and GUI

---

## Repository Layout

```
boulderdash/
├── Makefile
├── stonesandgem/
│   └── build/bin/gui
├── planners/
│   ├── forced-action-ff/ff
│   └── fast-downward/fast-downward.py
├── tools/
│   ├── plan.py
│   └── gui.py
├── pddl/
├── plan/
└── README.md
```

---

## Prerequisites

- macOS or Linux
- Python 3.9+
- CMake
- GNU Make
- C/C++ compiler

---

## Clone

```bash
git clone --recurse-submodules https://github.com/<you>/boulderdash.git
cd boulderdash
```

---

## Build

```bash
make
```

Clean:

```bash
make clean
make distclean
```

---

## Run GUI

```bash
python tools/gui.py
python tools/gui.py --level pddl/levels/level01.txt
```

---

## Planning

```bash
python tools/plan.py --domain pddl/domain.pddl --problem pddl/p01.pddl
```

Plans written to:

```
plan/p01/
```

Run FF only:

```bash
python tools/plan.py --planner ff --domain ... --problem ...
```

Run Fast Downward:

```bash
python tools/plan.py --planner fd --domain ... --problem ...
```

Stream output:

```bash
python tools/plan.py --planner fd --stream --domain ... --problem ...
```

Optimal FD plan:

```bash
python tools/plan.py --planner fd --optimal --domain ... --problem ...
```

---

## Level Encoding

```
0 Agent
1 Empty
2 Dirt
3 Stone
5 Gem
7 Wall
```
