# Test Problems

These files are generated from selected entries in `stonesandgem/bd_levels/bd_levels.txt`.

- Selected source levels: `1-3`, `6-9`, `11`, `13-14`
- One `.txt` file is emitted per target gem for all selected levels
- For level `1`, there is an additional start-target cross product over distinct
  gem pairs
- The files are intended to be passed back through the level generators as
  self-contained level text, without needing comment metadata

Filename format:

- `bd_level_<level-index>_target_gem_<row-major-gem-ordinal>.txt`
- `bd_level_01_start_gem_<row-major-gem-ordinal>_target_gem_<row-major-gem-ordinal>.txt`

Encoding:

- The target gem is marked in-grid using planner-only cell ID `90`
- A falling target gem would use planner-only cell ID `91`
- In `start_gem` variants, the agent is moved onto the chosen start gem cell
