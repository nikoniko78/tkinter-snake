mod_name = "Flashlight Mode"
mod_version = "10.4"
mod_description = "Cinematic flashlight mode with invisible aura, warm beam glow, smooth swing, and a true bright green snake head."

import math
from __main__ import CELL_SIZE

LIGHT_DISTANCE = 50
BEAM_WIDTH = 30
LIGHT_INTENSITY = 1.0
LIGHT_COLOR = (255, 230, 150)
FALLOFF_EXP = 1.5

SWING_SPEED = 0.16

AURA_RADIUS = 5
AURA_INTENSITY = 0.5
AURA_FALLOFF = 2.2

SEGMENT_LIGHT_COUNT = 6
BACKLIGHT_STRENGTH = 0.25
BACKLIGHT_FADE = 0.9

SNAKE_COLOR = (0, 255, 0)
HEAD_COLOR = (0, 255, 80)  # vivid luminous green
APPLE_COLOR = (255, 0, 0)
WALL_COLOR = (255, 255, 255)


def register():
    from __main__ import register_mode
    register_mode("Flashlight")


def direction_to_angle(direction):
    return {
        "Up": -math.pi / 2,
        "Down": math.pi / 2,
        "Left": math.pi,
        "Right": 0
    }.get(direction, 0)


def on_game_start(game):
    game._flashlight_angle = direction_to_angle(game.direction)
    game._target_angle = game._flashlight_angle


def on_60fps_update(game):
    if game.mode != "Flashlight":
        return
    if not hasattr(game, "_flashlight_angle"):
        game._flashlight_angle = direction_to_angle(game.direction)
        game._target_angle = game._flashlight_angle

    target = direction_to_angle(game.direction)
    current = game._flashlight_angle
    diff = (target - current + math.pi) % (2 * math.pi) - math.pi
    game._flashlight_angle += diff * SWING_SPEED


def clamp(x):
    return max(0, min(255, int(x)))


def apply_light(color_rgb, brightness, force_pure=False):
    """Apply lighting; if force_pure=True, skip warm light blending."""
    r, g, b = color_rgb
    if force_pure:
        r = clamp(r * brightness)
        g = clamp(g * brightness)
        b = clamp(b * brightness)
        return f"#{r:02x}{g:02x}{b:02x}"

    lr, lg, lb = LIGHT_COLOR
    r = clamp(r * brightness + lr * (1 - (1 - brightness)))
    g = clamp(g * brightness + lg * (1 - (1 - brightness)))
    b = clamp(b * brightness + lb * (1 - (1 - brightness)))
    return f"#{r:02x}{g:02x}{b:02x}"


def on_game_draw(game):
    if game.mode != "Flashlight":
        return

    c = game.canvas
    c.delete("all")

    head_x, head_y = game.snake[0]
    angle = getattr(game, "_flashlight_angle", direction_to_angle(game.direction))

    if game.mode == "Infinite":
        cx, cy = game.snake[0]
        offset_x = cx - game.view_w // 2
        offset_y = cy - game.view_h // 2
    else:
        offset_x, offset_y = 0, 0

    c.create_rectangle(0, 0, game.view_w * CELL_SIZE, game.view_h * CELL_SIZE, fill="black", outline="")

    flashlight_brightness = {}
    for gx in range(game.view_w):
        for gy in range(game.view_h):
            dx = gx - head_x
            dy = gy - head_y
            rot_x = dx * math.cos(angle) + dy * math.sin(angle)
            rot_y = -dx * math.sin(angle) + dy * math.cos(angle)
            if rot_x < 0 or rot_x > LIGHT_DISTANCE:
                continue
            max_side = (rot_x / LIGHT_DISTANCE) * (BEAM_WIDTH / 2)
            if abs(rot_y) <= max_side:
                dist_ratio = rot_x / LIGHT_DISTANCE
                brightness = (1 - dist_ratio) ** FALLOFF_EXP * LIGHT_INTENSITY
                flashlight_brightness[(gx, gy)] = max(0.0, min(1.0, brightness))

    aura_brightness = {}
    for gx in range(game.view_w):
        for gy in range(game.view_h):
            dx = gx - head_x
            dy = gy - head_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= AURA_RADIUS:
                brightness = (1 - (dist / AURA_RADIUS)) ** AURA_FALLOFF * AURA_INTENSITY
                aura_brightness[(gx, gy)] = max(0.0, min(1.0, brightness))

    visible = {}
    for gx in range(game.view_w):
        for gy in range(game.view_h):
            total = max(flashlight_brightness.get((gx, gy), 0),
                        aura_brightness.get((gx, gy), 0))
            if total > 0:
                visible[(gx, gy)] = total

    for gx in range(game.view_w):
        for gy in range(game.view_h):
            brightness = visible.get((gx, gy), 0)
            if brightness <= 0:
                continue

            draw_x = (gx - offset_x) * CELL_SIZE
            draw_y = (gy - offset_y) * CELL_SIZE

            if (gx, gy) in game.snake:
                index = game.snake.index((gx, gy))
                dist_from_head = math.sqrt((gx - head_x)**2 + (gy - head_y)**2)
                if dist_from_head > AURA_RADIUS + LIGHT_DISTANCE * 0.2:
                    continue
                if index == 0:
                    # brighter pure green head
                    color = apply_light(HEAD_COLOR, min(1.0, brightness * 1.3), force_pure=True)
                elif index < SEGMENT_LIGHT_COUNT:
                    seg_brightness = 1 - (index / SEGMENT_LIGHT_COUNT)
                    total_brightness = brightness * (0.6 + 0.4 * seg_brightness)
                    color = apply_light(SNAKE_COLOR, total_brightness)
                else:
                    fade = BACKLIGHT_STRENGTH * (BACKLIGHT_FADE ** (index - SEGMENT_LIGHT_COUNT))
                    total_brightness = brightness * fade
                    color = apply_light(SNAKE_COLOR, total_brightness)
                c.create_rectangle(draw_x, draw_y, draw_x + CELL_SIZE, draw_y + CELL_SIZE,
                                   fill=color, outline="")
                continue

            if (gx, gy) in game.apples:
                contrast = min(1.0, brightness * 1.8)
                r, g, b = APPLE_COLOR
                r = clamp(r * contrast + 80 * (1 - contrast))
                g = clamp(g * contrast * 0.4)
                b = clamp(b * contrast * 0.4)
                c.create_rectangle(draw_x, draw_y, draw_x + CELL_SIZE, draw_y + CELL_SIZE,
                                   fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
                continue

            if (gx, gy) in game.walls:
                w_brightness = brightness * 0.8
                gray = clamp(255 * w_brightness)
                outline = f"#{gray:02x}{gray:02x}{gray:02x}"
                c.create_rectangle(draw_x, draw_y, draw_x + CELL_SIZE, draw_y + CELL_SIZE,
                                   fill="black", outline=outline)
                continue

            if (gx, gy) in flashlight_brightness:
                r, g, b = LIGHT_COLOR
                r = int(r * (brightness ** 0.8))
                g = int(g * (brightness ** 0.8))
                b = int(b * (brightness ** 0.8))
                fill_color = f"#{r:02x}{g:02x}{b:02x}"
                c.create_rectangle(draw_x, draw_y, draw_x + CELL_SIZE, draw_y + CELL_SIZE,
                                   fill=fill_color, outline="")
