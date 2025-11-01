mod_name = "Shrinking Board"
mod_version = "6.3"
mod_description = "Rotating gradient shrinking border that smoothly transitions from yellow → red → purple, staying purple for the last 4 shrinks."

import math, random, time
from __main__ import CELL_SIZE, register_grid

BOARD_SIZE = 30
SHRINK_INTERVAL = 30.0
ROTATION_SPEED = 1.5
FLASH_COUNT = 5
FLASH_DURATION = 0.15
RING_THICKNESS = 1

# Color stops for smooth transition
COLOR_YELLOW = (255, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_PURPLE = (160, 0, 255)

# Gameplay constants
INITIAL_OFFSET = 3  # starting offset
FINAL_HOLD_STEPS = 4  # number of purple hold steps at end
TOTAL_SHRINKS = (BOARD_SIZE // 2) - INITIAL_OFFSET - FINAL_HOLD_STEPS  # active fading period

def register():
    register_grid("Shrinking", (BOARD_SIZE, BOARD_SIZE))

def should_run(game):
    return (
        game.mode != "Infinite"
        and game.view_w == BOARD_SIZE
        and game.view_h == BOARD_SIZE
    )

def on_game_start(game):
    if not should_run(game): return
    game._shrink_start_time = time.time()
    game._rotation_phase = 0.0
    game._border_offset = INITIAL_OFFSET
    game._next_shrink = SHRINK_INTERVAL
    game._flashing = False
    game._flash_start = None

def on_60fps_update(game):
    if not should_run(game): return
    game._rotation_phase += ROTATION_SPEED / 60.0
    elapsed = time.time() - game._shrink_start_time

    if not game._flashing and game._next_shrink - elapsed <= FLASH_COUNT * FLASH_DURATION * 2:
        game._flashing = True
        game._flash_start = time.time()

    if elapsed >= game._next_shrink:
        game._border_offset += 1
        game._next_shrink += SHRINK_INTERVAL
        game._flashing = False

def on_game_update(game):
    if not should_run(game): return

    try:
        o = game._border_offset
        hx, hy = game.snake[0]

        min_x = o
        max_x = BOARD_SIZE - o - 1
        min_y = o
        max_y = BOARD_SIZE - o - 1

        dx, dy = 0, 0
        if game.direction == "Left": dx = -1
        elif game.direction == "Right": dx = 1
        elif game.direction == "Up": dy = -1
        elif game.direction == "Down": dy = 1

        next_x = hx + dx
        next_y = hy + dy

        if getattr(game, "wrap", False):
            if next_x < min_x:
                hx = max_x
            elif next_x > max_x:
                hx = min_x
            if next_y < min_y:
                hy = max_y
            elif next_y > max_y:
                hy = min_y
            game.snake[0] = (hx, hy)
        else:
            if next_x < min_x or next_y < min_y or next_x > max_x or next_y > max_y:
                game.game_over()
                return

        game.apples = [a for a in game.apples if inside_safe(a, o)]
        while len(game.apples) < 1:
            game.apples.append(spawn_inner_apple(game, o))

    except ValueError as e:
        if "empty range" in str(e):
            print("[MOD ERROR] Shrinking board exceeded limits — killing player.")
            game.alive = False
        else:
            raise

def on_game_draw(game):
    if not should_run(game): return
    c = game.canvas
    c.delete("shrink_border_bg")

    o = game._border_offset
    phase = game._rotation_phase
    size = BOARD_SIZE * CELL_SIZE
    cx = size / 2
    cy = size / 2

    # --- Color stage logic (smooth fade with purple hold) ---
    def get_color(o):
        stage = max(o - INITIAL_OFFSET, 0)
        # t is normalized fade from 0 → 1 before the purple hold
        t = min(stage / float(TOTAL_SHRINKS), 1.0)

        if stage >= TOTAL_SHRINKS:  # final purple hold
            return COLOR_PURPLE
        elif t < 0.5:
            # yellow → red
            return interpolate_color(COLOR_YELLOW, COLOR_RED, t * 2)
        else:
            # red → purple
            return interpolate_color(COLOR_RED, COLOR_PURPLE, (t - 0.5) * 2)

    base_color = get_color(o)
    border_color_1 = base_color
    border_color_2 = (0, 0, 0)

    flash_color = None
    if game._flashing:
        t = time.time() - game._flash_start
        if int(t / FLASH_DURATION) % 2 == 0 and t < FLASH_COUNT * FLASH_DURATION * 2:
            # flash same hue, brighter
            flash_color = tuple(min(255, int(c * 1.5)) for c in base_color)
        elif t >= FLASH_COUNT * FLASH_DURATION * 2:
            game._flashing = False

    outer = o * CELL_SIZE
    step = CELL_SIZE

    def color_for_side(x, y):
        if flash_color:
            r, g, b = flash_color
            return f"#{r:02x}{g:02x}{b:02x}"
        dx = x - cx
        dy = y - cy
        angle = (math.atan2(dy, dx) + phase * 0.5)
        wave = (math.sin(angle * 6) * 0.5 + 0.5)
        r = int(border_color_1[0] * wave + border_color_2[0] * (1 - wave))
        g = int(border_color_1[1] * wave + border_color_2[1] * (1 - wave))
        b = int(border_color_1[2] * wave + border_color_2[2] * (1 - wave))
        return f"#{r:02x}{g:02x}{b:02x}"

    # --- Draw the ring edges ---
    for gx in range(BOARD_SIZE - o * 2):
        x = (o + gx) * CELL_SIZE
        y_top = outer
        y_bottom = size - outer - CELL_SIZE
        c.create_rectangle(x, y_top, x + step, y_top + step,
                           fill=color_for_side(x, y_top), outline="", tags="shrink_border_bg")
        c.create_rectangle(x, y_bottom, x + step, y_bottom + step,
                           fill=color_for_side(x, y_bottom), outline="", tags="shrink_border_bg")

    for gy in range(BOARD_SIZE - o * 2 - 2):
        y = (o + 1 + gy) * CELL_SIZE
        x_left = outer
        x_right = size - outer - CELL_SIZE
        c.create_rectangle(x_left, y, x_left + step, y + step,
                           fill=color_for_side(x_left, y), outline="", tags="shrink_border_bg")
        c.create_rectangle(x_right, y, x_right + step, y + step,
                           fill=color_for_side(x_right, y), outline="", tags="shrink_border_bg")

def on_game_draw_end(game):
    if not should_run(game): return
    c = game.canvas
    c.delete("shrinking_ui_text")
    score_text = f"Score: {game.score}"
    high_text = f"High Score: {game.highscore}"
    c.create_text(10, 10, anchor="nw", fill="white", font=("Consolas", 18, "bold"),
                  text=score_text, tags="shrinking_ui_text")
    c.create_text(10, 34, anchor="nw", fill="white", font=("Consolas", 14),
                  text=high_text, tags="shrinking_ui_text")

def inside_safe(pos, offset):
    x, y = pos
    return offset + 1 <= x < BOARD_SIZE - offset - 1 and offset + 1 <= y < BOARD_SIZE - offset - 1

def spawn_inner_apple(game, offset=0):
    x_min, x_max = offset + 1, BOARD_SIZE - offset - 2
    y_min, y_max = offset + 1, BOARD_SIZE - offset - 2

    if x_min >= x_max or y_min >= y_max:
        raise ValueError("Shrinking board too small to spawn apple")

    while True:
        ax = random.randint(x_min, x_max)
        ay = random.randint(y_min, y_max)
        if (ax, ay) not in game.snake and (ax, ay) not in game.walls:
            return (ax, ay)

def interpolate_color(c1, c2, t):
    """Linearly interpolate between two colors."""
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return (r, g, b)
