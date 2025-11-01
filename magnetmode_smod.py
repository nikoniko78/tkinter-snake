mod_name = "Magnet"
mod_version = "2.5"
mod_description = "Apples are smoothly pulled toward the snake’s head and grow it when eaten."

import math, random
from __main__ import CELL_SIZE, register_mode

MAGNET_RADIUS = 5.0      # how far the pull reaches
PULL_STRENGTH = 0.15     # acceleration per frame
FRICTION = 0.88          # velocity damping
EAT_DISTANCE = 0.6       # how close before eaten

def register():
    register_mode("Magnet")

def on_game_start(game):
    if game.mode != "Magnet":
        return
    # floating apple positions + velocities
    game._apple_float = {a: [float(a[0]), float(a[1])] for a in game.apples}
    game._apple_vels = {a: [0.0, 0.0] for a in game.apples}

def on_60fps_update(game):
    if game.mode != "Magnet":
        return
    if not hasattr(game, "_apple_float"):
        game._apple_float = {a: [float(a[0]), float(a[1])] for a in game.apples}
        game._apple_vels = {a: [0.0, 0.0] for a in game.apples}

    if not game.snake:
        return

    hx, hy = game.snake[0]
    eaten = []
    new_float = {}
    new_vels = {}

    for a, (fx, fy) in list(game._apple_float.items()):
        vx, vy = game._apple_vels.get(a, [0.0, 0.0])
        dx, dy = hx - fx, hy - fy
        dist = math.hypot(dx, dy)

        # Pull if within radius
        if 0.001 < dist <= MAGNET_RADIUS:
            pull = (1.0 - dist / MAGNET_RADIUS) * PULL_STRENGTH
            vx += (dx / dist) * pull
            vy += (dy / dist) * pull

        vx *= FRICTION
        vy *= FRICTION

        fx += vx
        fy += vy

        fx = max(0, min(game.view_w - 1, fx))
        fy = max(0, min(game.view_h - 1, fy))

        # Eat apple if close enough
        if dist <= EAT_DISTANCE:
            eaten.append(a)
            continue

        new_float[(fx, fy)] = [fx, fy]
        new_vels[(fx, fy)] = [vx, vy]

    # Apply new apple positions
    game._apple_float = new_float
    game._apple_vels = new_vels
    game.apples = [(round(x), round(y)) for x, y in new_float.keys()]

    # Handle eaten apples
    for _ in eaten:
        game.score += 1
        if game.score > game.highscore:
            game.highscore = game.score

        # --- 🔥 Force immediate snake growth ---
        if len(game.snake) > 0:
            tail = game.snake[-1]
            game.snake.append(tail)  # add one more segment instantly

        # spawn new apple
        new_apple = spawn_new_apple(game)
        game.apples.append(new_apple)
        game._apple_float[new_apple] = [float(new_apple[0]), float(new_apple[1])]
        game._apple_vels[new_apple] = [0.0, 0.0]

def on_game_update(game):
    if game.mode != "Magnet":
        return
    # keep apples valid
    game.apples = [a for a in game.apples if 0 <= a[0] < game.view_w and 0 <= a[1] < game.view_h]

def spawn_new_apple(game):
    while True:
        x = random.randint(0, game.view_w - 1)
        y = random.randint(0, game.view_h - 1)
        if (x, y) not in game.snake and (x, y) not in game.walls:
            return (x, y)
