# ==========================================================
# Boulderdash top-level Makefile
# ==========================================================

.PHONY: all planners game ff fd clean distclean help

# ---- Paths ----
GAME_DIR := stonesandgem
FF_DIR   := planners/forced-action-ff
FD_DIR   := planners/fast-downward

# ---- Default target ----
all: planners game

# ==========================================================
# Planners
# ==========================================================

planners: ff fd

ff:
	@echo "==> Building Forced-Action FF"
	$(MAKE) -C $(FF_DIR)

fd:
	@echo "==> Building Forced-Action Fast Downward"
	cd $(FD_DIR) && ./build.py

# ==========================================================
# Game
# ==========================================================

game:
	@echo "==> Building Stones & Gems (CMake)"
	mkdir -p $(GAME_DIR)/build
	cd $(GAME_DIR)/build && cmake .. && $(MAKE)

# ==========================================================
# Cleanup
# ==========================================================

clean:
	@echo "==> Cleaning Stones & Gems"
	-rm -rf $(GAME_DIR)/build

	@echo "==> Cleaning Forced-Action FF"
	-$(MAKE) -C $(FF_DIR) clean


distclean: clean
	@echo "==> Removing FD build directory"
	-rm -rf $(FD_DIR)/build

# ==========================================================
# Help
# ==========================================================

help:
	@echo ""
	@echo "Boulderdash build targets:"
	@echo ""
	@echo "  make            Build everything"
	@echo "  make planners   Build all planners"
	@echo "  make ff         Build Forced-Action FF"
	@echo "  make fd         Build Forced-Action Fast Downward"
	@echo "  make game       Build Stones & Gems"
	@echo "  make clean      Clean builds"
	@echo "  make distclean  Deep clean (includes FD build dir)"
	@echo ""
