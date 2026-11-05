// Batch tracer for the stonesngems engine (the source of truth).
//
// Reads one case per line on stdin:
//   <level string>;<action digits>;<tracked cell index or -1>
// level:   rows|cols|max_steps|gems|cell0|cell1|...   (engine cell ids)
// actions: 0=noop 1=up 2=right 3=down 4=left (may be empty)
// tracked: index of a stone/gem whose engine object id is followed over time
//          (used for the planner's target gem); -1 to disable.
//
// For each case prints:
//   CASE <n>
//   T <tick> <status> <gems_collected> <tracked_index> <cell0>,<cell1>,...
//   END
// tick 0 is the initial state. status: A alive, D dead, X in exit, O out of time.
// tracked_index is -1 once the tracked object no longer exists (e.g. collected).
//
// Build (from repo root):
//   g++ -std=c++20 -O2 -Istonesandgem/src tools/sim_check/engine_trace.cpp \
//       stonesandgem/src/stonesngems_base.cpp stonesandgem/src/util.cpp \
//       -o tools/sim_check/build/engine_trace

#include <iostream>
#include <limits>
#include <sstream>
#include <string>

#include "stonesngems_base.h"

using namespace stonesngems;

namespace {

void dump(const RNDGameState &state, int tick, std::size_t n_cells, int gems, int tracked_id) {
    char status = 'A';
    const auto pos = state.get_agent_pos();
    if (pos == kAgentPosDie) {
        status = 'D';
    } else if (pos == kAgentPosExit) {
        status = 'X';
    } else if (state.is_terminal()) {
        status = 'O';
    }
    long long tracked_idx = -1;
    if (tracked_id >= 0) {
        const auto idx = state.get_id_index(tracked_id);
        if (idx != std::numeric_limits<std::size_t>::max()) tracked_idx = static_cast<long long>(idx);
    }
    std::cout << "T " << tick << ' ' << status << ' ' << gems << ' ' << tracked_idx << ' ';
    for (std::size_t i = 0; i < n_cells; ++i) {
        if (i) std::cout << ',';
        std::cout << static_cast<int>(state.get_hidden_item(i));
    }
    std::cout << '\n';
}

}    // namespace

int main() {
    std::ios::sync_with_stdio(false);
    std::string line;
    int case_no = 0;
    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string level, actions, tracked_str;
        std::getline(ss, level, ';');
        std::getline(ss, actions, ';');
        std::getline(ss, tracked_str, ';');
        const long long tracked_cell = tracked_str.empty() ? -1 : std::stoll(tracked_str);

        GameParameters params = kDefaultGameParams;
        params["game_board_str"] = GameParameter(level);
        RNDGameState state(params);
        const auto shape = state.observation_shape();
        const std::size_t n_cells = shape[1] * shape[2];
        const int tracked_id =
            tracked_cell >= 0 ? state.get_index_id(static_cast<std::size_t>(tracked_cell)) : -1;

        std::cout << "CASE " << case_no++ << '\n';
        int gems = 0;
        dump(state, 0, n_cells, gems, tracked_id);
        int tick = 0;
        for (char ch : actions) {
            if (ch < '0' || ch > '4') continue;
            state.apply_action(static_cast<Action>(ch - '0'));
            if (state.get_reward_signal() & kRewardCollectDiamond) ++gems;
            dump(state, ++tick, n_cells, gems, tracked_id);
        }
        std::cout << "END\n";
    }
    return 0;
}
