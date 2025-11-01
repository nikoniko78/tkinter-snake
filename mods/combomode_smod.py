mod_name = "Combo Fever Mode"
mod_version = "1.1"
mod_description = "Chain apples fast to build score multipliers. Miss a few seconds and the combo resets!"

import time
import traceback

def on_menu_open(root, canvas, options, modes, grids, submenus):
    """Add Combo Fever mode to the menu."""
    try:
        if "Combo Fever" not in modes:
            modes.append("Combo Fever")
    except Exception as e:
        print("[Combo Fever] Error in on_menu_open:", e)
        traceback.print_exc()


def on_game_start(game):
    """Initialize combo variables when Combo Fever starts."""
    try:
        if getattr(game, "mode", "") != "Combo Fever":
            return
        game.combo_multiplier = 1
        game.last_apple_time = time.time()
        game.combo_timeout = 3  # seconds allowed between apples
        game._prev_score = game.score
    except Exception as e:
        print("[Combo Fever] Error in on_game_start:", e)
        traceback.print_exc()


def on_game_update(game):
    """Check for apple chain combos."""
    try:
        if getattr(game, "mode", "") != "Combo Fever":
            return

        now = time.time()

        # Reset combo if timeout exceeded
        if now - game.last_apple_time > game.combo_timeout:
            game.combo_multiplier = 1

        # Detect apple eaten by score difference
        if not hasattr(game, "_prev_score"):
            game._prev_score = game.score

        if game.score > game._prev_score:
            # Apple eaten: apply combo bonus
            game.last_apple_time = now
            game.combo_multiplier = min(game.combo_multiplier + 1, 10)
            gained = game.score - game._prev_score
            bonus = gained * (game.combo_multiplier - 1)
            game.score += bonus

        game._prev_score = game.score

    except Exception as e:
        print("[Combo Fever] Error in on_game_update:", e)
        traceback.print_exc()


def on_game_draw(game):
    """Draw combo info on screen."""
    try:
        if getattr(game, "mode", "") != "Combo Fever":
            return

        c = game.canvas
        combo = getattr(game, "combo_multiplier", 1)
        if combo > 1:
            color = (
                "yellow" if combo < 5 else
                "orange" if combo < 8 else
                "red"
            )
            c.create_text(
                game.view_w * 20 - 10, 10,
                anchor="ne",
                fill=color,
                font=("Courier", 16, "bold"),
                text=f"COMBO x{combo}"
            )
    except Exception as e:
        print("[Combo Fever] Error in on_game_draw:", e)
        traceback.print_exc()
