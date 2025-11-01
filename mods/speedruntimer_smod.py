mod_name = "Speedrun Timer"
mod_version = "1.3"
mod_description = "Adds a yellow speedrun timer to the bottom-right corner and shows final time on Game Over."

import time
from __main__ import CELL_SIZE


run_start = None
final_time_str = ""


def on_game_start(game):
    """Start timer when the game begins, and patch game_over() so we can draw at the right time."""
    global run_start, final_time_str
    run_start = time.time()
    final_time_str = ""

    original_game_over = game.game_over

    # Wrap game_over to inject our timer
    def patched_game_over():
        original_game_over()

        total = time.time() - run_start
        mins = int(total // 60)
        secs = int(total % 60)
        ms = int((total * 1000) % 1000)
        final_time_str = f"{mins:02}:{secs:02}.{ms:03}"

        # Draw final timer after the game over screen
        game.canvas.create_text(
            game.view_w * CELL_SIZE / 2,
            game.view_h * CELL_SIZE / 2 + 60,
            fill="yellow",
            font=("Courier", 20, "bold"),
            text=f"Final Time: {final_time_str}",
        )

    game.game_over = patched_game_over


def on_game_draw(game):
    """Draw the live timer while playing."""
    global run_start
    if not game.running or run_start is None:
        return

    elapsed = time.time() - run_start
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    ms = int((elapsed * 1000) % 1000)
    time_str = f"{mins:02}:{secs:02}.{ms:03}"

    canvas = game.canvas
    w = game.view_w * CELL_SIZE
    h = game.view_h * CELL_SIZE

    canvas.create_text(
        w - 10,
        h - 10,
        anchor="se",
        fill="yellow",
        font=("Courier", 16, "bold"),
        text=time_str,
    )
