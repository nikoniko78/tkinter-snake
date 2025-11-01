# Speedrun Mode Mod
# Adds a "Speedrun" mode that behaves like Normal but fills the grid with apples.
# Guaranteed not to affect any other modes.

mod_name = "Speedrun Mode"
mod_version = "1.2"
mod_description = "Behaves like Normal mode but spawns tons of apples for fast scoring."

def on_menu_open(root, canvas, options, modes, grids, submenus):
    # Add Speedrun mode safely without duplicates
    if "Speedrun" not in modes:
        modes.append("Speedrun")


def on_game_start(game):
    # Only run this mod if the selected mode is Speedrun
    if not hasattr(game, "mode") or game.mode != "Speedrun":
        return

    # Safely import constants from main game
    from __main__ import GRID_WIDTH, GRID_HEIGHT

    # Clear only Speedrun apples
    apple_count = max(1, (GRID_WIDTH * GRID_HEIGHT) // 20)
    new_apples = []
    for _ in range(apple_count):
        pos = game.spawn_food()
        if pos not in new_apples:
            new_apples.append(pos)

    # Replace apples only in Speedrun mode
    game.apples = new_apples


def on_game_update(game):
    # Only affect Speedrun mode
    if getattr(game, "mode", "") != "Speedrun":
        return
    # No behavior change yet (reserved for future updates)
    pass


def on_game_draw(game):
    # Only affect Speedrun mode visuals
    if getattr(game, "mode", "") != "Speedrun":
        return
    # Example overlay label
    game.canvas.create_text(10, 50, anchor="nw", fill="cyan",
                            font=("Courier", 14, "bold"),
                            text="SPEEDRUN MODE")
