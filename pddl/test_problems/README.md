# Test Problems

These files are generated from selected entries in `stonesandgem/bd_levels/bd_levels.txt`.

- Selected source levels: `1-3`, `6-9`, `11`, `13-14`
- One `.txt` file is emitted per target gem for all selected levels
- For level `1`, there is an additional full start-target cross product:
  `start-gem-ordinal x target-gem-ordinal`
- The files are intended to be passed back through the level generators, which now
  understand `start-gem-ordinal` and `target-gem-ordinal` comment metadata

Filename format:

- `bd_level_<level-index>_target_gem_<row-major-gem-ordinal>.txt`
- `bd_level_01_start_gem_<row-major-gem-ordinal>_target_gem_<row-major-gem-ordinal>.txt`

Each generated level file starts with comments recording:

- the source line in `bd_levels.txt`
- the target gem ordinal within that level
- the total gem count
- optionally the start gem ordinal when the agent start is overridden
