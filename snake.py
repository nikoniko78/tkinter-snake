import tkinter as tk
import random
import math
import colorsys
import json
import os
import time
import importlib.util

CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 30

speeds = ["Slow", "Medium", "Fast"]
speed_values = {"Slow": 150, "Medium": 100, "Fast": 70}
grids = ["Small", "Medium", "Large"]
grid_values = {"Small": (19, 19), "Medium": (24, 24), "Large": (29, 29)}
wraps = ["Off", "On"]
modes = ["Normal", "Progressive", "Infinite", "Timed", "Shrink", "Wall"]

menu_index = 0
speed_index = 1
grid_index = 1
wrap_index = 0
mode_index = 0

SAVE_FILE = "highscores.txt"
MODS_DIR = "snakemods"

if not os.path.exists(MODS_DIR):
    os.makedirs(MODS_DIR)

highscores = {}


def load_highscores():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_highscores(highscores):
    with open(SAVE_FILE, "w") as f:
        json.dump(highscores, f)


highscores = load_highscores()

# -------------------------
# MOD SUPPORT SYSTEM
# -------------------------
loaded_mods = []

def call_mod_hook(hook_name, *args, **kwargs):
    """Call a specific hook on all loaded mods if they define it."""
    for mod in loaded_mods:
        func = getattr(mod, hook_name, None)
        if callable(func):
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"[MOD ERROR] in {mod.__name__}.{hook_name}: {e}")

def register_mode(name):
    if name not in modes:
        modes.append(name)

def register_speed(name, delay):
    if name not in speeds:
        speeds.append(name)
        speed_values[name] = delay

def register_grid(name, size):
    if name not in grids:
        grids.append(name)
        grid_values[name] = size

def register_wrap(name):
    if name not in wraps:
        wraps.append(name)

def load_mods():
    """Load all .py files from snakemods folder."""
    for fname in os.listdir(MODS_DIR):
        if fname.endswith(".py"):
            mod_path = os.path.join(MODS_DIR, fname)
            mod_name = fname[:-3]
            try:
                spec = importlib.util.spec_from_file_location(mod_name, mod_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                loaded_mods.append(mod)
                print(f"[MOD] Loaded {mod_name}")
                if hasattr(mod, "register"):
                    mod.register()
            except Exception as e:
                print(f"[MOD ERROR] Failed to load {mod_name}: {e}")

# Load all mods at startup
load_mods()

# -------------------------
# GAME CLASS
# -------------------------
class SnakeGame:

    def draw_ui(self):
        """Ensure the UI (score, high score, timers) draws last, above all mods."""
        try:
            if hasattr(self, 'draw_score'):
                self.draw_score()
            if hasattr(self, 'draw_highscore'):
                self.draw_highscore()
            if hasattr(self, 'draw_timer'):
                self.draw_timer()
        except Exception as e:
            print('[UI ERROR]', e)

    def __init__(self, root, speed, grid, wrap, mode):
        self.root = root
        self.root.title("Snake Game")
        self.running = False
        self.wrap = wrap
        self.mode = mode
        self.highscores = highscores
        self.highscore = self.highscores.get(self.mode, 0)
        self.beat_highscore = False
        self.start_time = time.time()
        self.walls = []

        if self.mode == "Infinite":
            self.wrap = True
            grid = (200, 200)

        global GRID_WIDTH, GRID_HEIGHT
        GRID_WIDTH, GRID_HEIGHT = grid

        if self.mode == "Infinite":
            self.view_w, self.view_h = grid_values["Medium"]
        else:
            self.view_w, self.view_h = GRID_WIDTH, GRID_HEIGHT

        width = self.view_w * CELL_SIZE
        height = self.view_h * CELL_SIZE
        self.canvas = tk.Canvas(root, width=width, height=height, bg="black")
        self.canvas.pack()

        root.update_idletasks()
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")

        self.direction = "Right"
        start_x, start_y = GRID_WIDTH // 2, GRID_HEIGHT // 2
        if self.mode == "Infinite":
            self.snake = [(start_x - i, start_y) for i in range(3)]
        else:
            self.snake = [(start_x, start_y)]

        if self.mode == "Infinite":
            self.apples = self.spawn_multiple_apples()
        else:
            self.apples = [self.spawn_food()]

        self.base_speed = speed_values[speed]
        self.speed = self.base_speed
        self.score = 0
        self.frame_count = 0
        self.last_shrink_time = time.time()

        self.time_limit = 10
        self.last_time_update = time.time()
        self.shrink_timer_active = False
        self.shrink_timer_start = None
        self.shrink_timer_limit = 5

        self.root.bind("<Up>", lambda e: self.change_direction("Up"))
        self.root.bind("<Down>", lambda e: self.change_direction("Down"))
        self.root.bind("<Left>", lambda e: self.change_direction("Left"))
        self.root.bind("<Right>", lambda e: self.change_direction("Right"))
        self.root.bind("<Return>", lambda e: self.restart())
        self.root.bind("<Escape>", lambda e: self.quit())

        self.running = True
        call_mod_hook("on_game_start", self)

        # Start both loops
        self.root.after(self.speed, self.update)       # Snake movement loop
        self.root.after(16, self.frame_update)         # 60 FPS loop

    def spawn_food(self):
        while True:
            pos = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if pos not in self.snake and pos not in self.walls:
                return pos

    def spawn_multiple_apples(self):
        apple_count = max(1, (GRID_WIDTH * GRID_HEIGHT) // 100)
        apples = []
        for _ in range(apple_count):
            apples.append(self.spawn_food())
        return apples

    def change_direction(self, new_dir):
        opposites = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
        if opposites.get(self.direction) != new_dir:
            self.direction = new_dir

    def frame_update(self):
        """Runs at 60 FPS for animations, timers, and mod hooks (not movement)."""
        if not self.running:
            return
        self.frame_count += 1
        self.draw()
        call_mod_hook("on_60fps_update", self)
        call_mod_hook("on_frame_update", self)
        self.draw_ui()
        self.root.after(16, self.frame_update)  # 60 FPS loop

    def update(self):
        if not self.running:
            return

        call_mod_hook("on_game_update", self)

        now = time.time()
        if self.mode == "Timed":
            elapsed = now - self.start_time
            remaining = self.time_limit - int(elapsed)
            if remaining <= 0:
                self.game_over()
                return

        if self.mode == "Shrink":
            if now - self.last_shrink_time > 5:
                if len(self.snake) > 1:
                    self.snake.pop()
                self.last_shrink_time = now
            if len(self.snake) == 1:
                if not self.shrink_timer_active:
                    self.shrink_timer_active = True
                    self.shrink_timer_start = now
            else:
                self.shrink_timer_active = False
            if self.shrink_timer_active and now - self.shrink_timer_start >= self.shrink_timer_limit:
                self.game_over()
                return

        head_x, head_y = self.snake[0]
        if self.direction == "Up":
            head_y -= 1
        elif self.direction == "Down":
            head_y += 1
        elif self.direction == "Left":
            head_x -= 1
        elif self.direction == "Right":
            head_x += 1

        if self.wrap:
            head_x %= GRID_WIDTH
            head_y %= GRID_HEIGHT
        else:
            if not (0 <= head_x < GRID_WIDTH and 0 <= head_y < GRID_HEIGHT):
                self.game_over()
                return

        new_head = (head_x, head_y)
        if new_head in self.walls or new_head in self.snake:
            self.game_over()
            return

        self.snake.insert(0, new_head)
        if new_head in self.apples:
            self.apples.remove(new_head)
            if self.mode != "Infinite":
                self.apples.append(self.spawn_food())
            self.score += 1
            if self.mode == "Timed":
                self.time_limit += 3
            if self.mode == "Shrink":
                self.shrink_timer_active = False
            if self.mode == "Wall":
                wall = self.spawn_food()
                self.walls.append(wall)
            if self.score > self.highscore:
                self.highscore = self.score
                self.beat_highscore = True
                self.highscores[self.mode] = self.highscore
                save_highscores(self.highscores)
            if self.mode == "Progressive":
                self.speed = max(40, int(self.base_speed * (0.95 ** self.score)))
        else:
            self.snake.pop()

        self.root.after(self.speed, self.update)

    
    def draw(self):
        self.canvas.delete("all")

        # Determine offset for Infinite mode
        if self.mode == "Infinite":
            cx, cy = self.snake[0]
            offset_x = cx - self.view_w // 2
            offset_y = cy - self.view_h // 2
        else:
            offset_x, offset_y = 0, 0

        # Background fill
        self.canvas.create_rectangle(
            0, 0, self.view_w * CELL_SIZE, self.view_h * CELL_SIZE,
            fill="black", outline=""
        )

        t = time.time()
        rainbow_mode = self.beat_highscore

        # Snake body
        for i, (x, y) in enumerate(self.snake):
            draw_x = (x - offset_x) * CELL_SIZE
            draw_y = (y - offset_y) * CELL_SIZE

            if 0 <= draw_x < self.view_w * CELL_SIZE and 0 <= draw_y < self.view_h * CELL_SIZE:
                if rainbow_mode:
                    # Slower rainbow hue animation (matches mod style)
                    hue = (i * 0.02 + t * 0.25) % 1.0
                    r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1, 1)]
                    color = f"#{r:02x}{g:02x}{b:02x}"
                else:
                    # Regular green pulse animation
                    wave = math.sin(i * 0.3 + t * 2)
                    base_g = int(140 + 90 * wave)
                    base_g = max(80, min(255, base_g))
                    color = f"#00{base_g:02x}00"

                self.canvas.create_rectangle(
                    draw_x, draw_y,
                    draw_x + CELL_SIZE, draw_y + CELL_SIZE,
                    fill=color, outline="black"
                )

        # Apples
        for fx, fy in self.apples:
            draw_x = (fx - offset_x) * CELL_SIZE
            draw_y = (fy - offset_y) * CELL_SIZE
            if 0 <= draw_x < self.view_w * CELL_SIZE and 0 <= draw_y < self.view_h * CELL_SIZE:
                self.canvas.create_rectangle(
                    draw_x, draw_y,
                    draw_x + CELL_SIZE, draw_y + CELL_SIZE,
                    fill="red", outline="black"
                )

        # Walls
        for wx, wy in self.walls:
            draw_x = (wx - offset_x) * CELL_SIZE
            draw_y = (wy - offset_y) * CELL_SIZE
            if 0 <= draw_x < self.view_w * CELL_SIZE and 0 <= draw_y < self.view_h * CELL_SIZE:
                self.canvas.create_rectangle(
                    draw_x, draw_y,
                    draw_x + CELL_SIZE, draw_y + CELL_SIZE,
                    fill="black", outline="white"
                )

        # Score text
        self.canvas.create_text(
            10, 10, anchor="nw", fill="white",
            font=("Courier", 14), text=f"Score: {self.score}"
        )

        # High score text (slower rainbow animation)
        color = "yellow"
        if self.beat_highscore:
            hue = (t * 0.25) % 1.0
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1, 1)]
            color = f"#{r:02x}{g:02x}{b:02x}"

        self.canvas.create_text(
            10, 30, anchor="nw", fill=color,
            font=("Courier", 14),
            text=f"High Score ({self.mode}): {self.highscore}"
        )

        # Mod hook for custom draw logic
        call_mod_hook("on_game_draw", self)

        # Timed mode countdown
        if self.mode == "Timed":
            remaining = max(0, self.time_limit - int(time.time() - self.start_time))
            self.canvas.create_text(
                self.view_w * CELL_SIZE - 10, 10,
                anchor="ne", fill="red",
                font=("Courier", 16, "bold"),
                text=f"{remaining}s"
            )

        # Shrink mode timer
        if self.mode == "Shrink" and self.shrink_timer_active:
            elapsed = time.time() - self.shrink_timer_start
            remaining = max(0, self.shrink_timer_limit - elapsed)
            self.canvas.create_text(
                self.view_w * CELL_SIZE - 10, 10,
                anchor="ne", fill="red",
                font=("Courier", 16, "bold"),
                text=f"{remaining:.1f}s"
            )

        # Ensure UI text always drawn last (above all mods)
        self.canvas.lift("all")




    def game_over(self):
        self.running = False
        self.canvas.delete("all")
        self.canvas.create_text(self.view_w * CELL_SIZE / 2, self.view_h * CELL_SIZE / 2 - 20,
                                fill="white", font=("Courier", 24), text="GAME OVER")
        self.canvas.create_text(self.view_w * CELL_SIZE / 2, self.view_h * CELL_SIZE / 2 + 20,
                                fill="white", font=("Courier", 18), text="Press Enter to return to Menu")
        call_mod_hook("on_game_end", self)

    def restart(self):
        if not self.running:
            self.canvas.destroy()
            show_menu(self.root)

    def quit(self):
        self.root.destroy()

def show_menu(root):
    global menu_index, speed_index, grid_index, wrap_index, mode_index
    canvas = tk.Canvas(root, width=600, height=600, bg="black")
    canvas.pack()

    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w // 2) - 300
    y = (screen_h // 2) - 300
    root.geometry(f"600x600+{x}+{y}")

    options = ["Speed", "Grid Size", "Wrap Around", "Mode", "Start Game"]

    def draw_menu():
        import colorsys

        canvas.delete("all")
        canvas.create_text(300, 100, text="SNAKE GAME", fill="white", font=("Courier", 36))

        # ⚪ Game version (top center)
        canvas.create_text(
            300, 17,
            text="v3.7.12",
            fill="white",
            font=("Courier", 10, "bold")
        )

        y = 250
        for i, opt in enumerate(options):
            prefix = ">" if i == menu_index else " "
            if opt == "Speed":
                val = speeds[speed_index]
            elif opt == "Grid Size":
                val = grids[grid_index]
            elif opt == "Wrap Around":
                val = wraps[wrap_index]
            elif opt == "Mode":
                val = modes[mode_index]
            else:
                val = ""
            text = f"{prefix} {opt}: {val}" if val else f"{prefix} {opt}"
            color = "white"
            if opt == "Mode" and val in ["Infinite", "Wall", "Timed", "Shrink"]:
                color = "#ffffff"
            canvas.create_text(300, y + i * 40, text=text,
                               fill=color if i != menu_index else "green",
                               font=("Courier", 20))

        mode = modes[mode_index]
        current_high = highscores.get(mode, 0)
        canvas.create_text(300, 500, text=f"High Score ({mode}): {current_high}",
                           fill="yellow", font=("Courier", 16))

        # 🔴 Warning text for multiple mods (top-right)
        if len(loaded_mods) > 1:
            canvas.create_text(590, 10, anchor="ne",
                               text="Multiple mods active!\nMinor glitches may occur.",
                               fill="red", font=("Courier", 10, "bold"))

        # 🌈 Static rainbow "Made by Remi Lo Casto" (top-left)
        name = "Remi Lo Casto"
        hue_step = 1.0 / len(name)
        canvas.create_text(10, 27, anchor="sw", text="Made by", fill="white",
                           font=("Courier", 12, "bold"))
        for i, ch in enumerate(name):
            hue = i * hue_step
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1, 1)]
            color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_text(85 + i * 9, 27, anchor="sw",
                               text=ch, fill=color, font=("Courier", 12, "bold"))

        # 🟦 Instruction text (bottom center)
        canvas.create_text(
            300, 580,
            text="Double tap PageDown/Zero or press Esc to close.",
            fill="cyan",
            font=("Courier", 12, "bold")
        )

        root.update()

    def up(e):
        global menu_index
        menu_index = (menu_index - 1) % len(options)
        draw_menu()

    def down(e):
        global menu_index
        menu_index = (menu_index + 1) % len(options)
        draw_menu()

    def left(e):
        global speed_index, grid_index, wrap_index, mode_index
        if options[menu_index] == "Speed":
            speed_index = (speed_index - 1) % len(speeds)
        elif options[menu_index] == "Grid Size":
            grid_index = (grid_index - 1) % len(grids)
        elif options[menu_index] == "Wrap Around":
            wrap_index = (wrap_index - 1) % len(wraps)
        elif options[menu_index] == "Mode":
            mode_index = (mode_index - 1) % len(modes)
        draw_menu()

    def right(e):
        global speed_index, grid_index, wrap_index, mode_index
        if options[menu_index] == "Speed":
            speed_index = (speed_index + 1) % len(speeds)
        elif options[menu_index] == "Grid Size":
            grid_index = (grid_index + 1) % len(grids)
        elif options[menu_index] == "Wrap Around":
            wrap_index = (wrap_index + 1) % len(wraps)
        elif options[menu_index] == "Mode":
            mode_index = (mode_index + 1) % len(modes)
        draw_menu()

    def select(e):
        if options[menu_index] == "Start Game":
            canvas.destroy()
            SnakeGame(root, speeds[speed_index],
                      grid_values[grids[grid_index]],
                      wraps[wrap_index] == "On",
                      modes[mode_index])

    last_pagedown_time = [0]  # use list to mutate inside nested func

    def on_pagedown(e):
        now = time.time()
        if now - last_pagedown_time[0] <= 1:
            root.destroy()
        else:
            last_pagedown_time[0] = now

    root.bind("<Up>", up)
    root.bind("<Down>", down)
    root.bind("<Left>", left)
    root.bind("<Right>", right)
    root.bind("<Return>", select)
    root.bind("<Escape>", lambda e: root.destroy())
    root.bind("<Next>", on_pagedown)  # double-tap Page Down to close
    root.bind("<0>", on_pagedown)


    draw_menu()
    call_mod_hook("on_menu_open", root, canvas, options, modes, grids, wraps)

root = tk.Tk()
show_menu(root)
root.mainloop()
