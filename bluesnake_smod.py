mod_name = "Blue Gradient Snake"
mod_version = "1.4"
mod_description = "Snake has a blue gradient and turns rainbow on high score, with a black background and light-blue wall outlines."

import colorsys
import math
import time
from __main__ import CELL_SIZE  # Use global constant safely

def on_game_draw(game):
    """Draw the snake with a blue gradient, rainbow when beating a high score, on a black background with light-blue wall outlines."""
    c = game.canvas
    c.delete("all")

    # Handle Infinite mode offset
    if game.mode == "Infinite":
        cx, cy = game.snake[0]
        offset_x = cx - game.view_w // 2
        offset_y = cy - game.view_h // 2
    else:
        offset_x, offset_y = 0, 0

    # Background (pure black)
    c.create_rectangle(0, 0, game.view_w * CELL_SIZE, game.view_h * CELL_SIZE, fill="black", outline="")

    rainbow_mode = game.score >= game.highscore
    t = time.time()

    # Snake body
    for i, (x, y) in enumerate(game.snake):
        draw_x = (x - offset_x) * CELL_SIZE
        draw_y = (y - offset_y) * CELL_SIZE

        if 0 <= draw_x < game.view_w * CELL_SIZE and 0 <= draw_y < game.view_h * CELL_SIZE:
            if rainbow_mode:
                # Slower rainbow hue
                hue = (i * 0.02 + t * 0.25) % 1.0
            else:
                # Keep blue gradient pulse the same
                wave = math.sin(i * 0.3 + t * 1.5)
                hue = 0.6 + 0.05 * wave
            r, g, b = [int(v * 255) for v in colorsys.hsv_to_rgb(hue, 1, 1)]
            color = f"#{r:02x}{g:02x}{b:02x}"

            c.create_rectangle(draw_x, draw_y,
                               draw_x + CELL_SIZE, draw_y + CELL_SIZE,
                               fill=color, outline="black")

    # Apples stay red
    for fx, fy in game.apples:
        draw_x = (fx - offset_x) * CELL_SIZE
        draw_y = (fy - offset_y) * CELL_SIZE
        if 0 <= draw_x < game.view_w * CELL_SIZE and 0 <= draw_y < game.view_h * CELL_SIZE:
            c.create_rectangle(draw_x, draw_y,
                               draw_x + CELL_SIZE, draw_y + CELL_SIZE,
                               fill="red", outline="black")

    # Walls: black fill, light-blue outline
    for wx, wy in game.walls:
        draw_x = (wx - offset_x) * CELL_SIZE
        draw_y = (wy - offset_y) * CELL_SIZE
        if 0 <= draw_x < game.view_w * CELL_SIZE and 0 <= draw_y < game.view_h * CELL_SIZE:
            c.create_rectangle(draw_x, draw_y,
                               draw_x + CELL_SIZE, draw_y + CELL_SIZE,
                               fill="black", outline="#33ccff")

    # Score text
    c.create_text(10, 10, anchor="nw", fill="white", font=("Courier", 14),
                  text=f"Score: {game.score}")

    # High score text (slower rainbow)
    if rainbow_mode:
        hue = (t * 0.25) % 1.0
        r, g, b = [int(v * 255) for v in colorsys.hsv_to_rgb(hue, 1, 1)]
        color = f"#{r:02x}{g:02x}{b:02x}"
    else:
        color = "cyan"

    c.create_text(10, 30, anchor="nw", fill=color, font=("Courier", 14),
                  text=f"High Score ({game.mode}): {game.highscore}")
