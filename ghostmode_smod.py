mod_name = "Ghost Mode"
mod_version = "1.0"
mod_description = "A gamemode where you can pass through yourself, but still hit walls."

def on_menu_open(root, canvas, options, modes, grids, submenus):
    """Add Ghost Mode to the game mode list."""
    if "Ghost" not in modes:
        modes.append("Ghost")


def on_game_start(game):
    """Patch the collision logic for Ghost Mode."""
    if getattr(game, "mode", "") != "Ghost":
        return

    # Store original update method
    original_update = game.update

    def ghost_update(self):
        """Modified update: ignores self-collisions."""
        if not self.running:
            return

        # Save head and direction
        head_x, head_y = self.snake[0]

        # Movement update logic from original
        if self.direction == "Up":
            head_y -= 1
        elif self.direction == "Down":
            head_y += 1
        elif self.direction == "Left":
            head_x -= 1
        elif self.direction == "Right":
            head_x += 1

        # Handle wrapping or out-of-bounds
        if self.wrap:
            head_x %= self.GRID_WIDTH if hasattr(self, "GRID_WIDTH") else self.view_w
            head_y %= self.GRID_HEIGHT if hasattr(self, "GRID_HEIGHT") else self.view_h
        else:
            if not (0 <= head_x < self.view_w and 0 <= head_y < self.view_h):
                self.game_over()
                return

        new_head = (head_x, head_y)

        # ❌ Ignore self-collision (Ghost mode)
        if new_head in self.walls:
            self.game_over()
            return

        self.snake.insert(0, new_head)

        # Handle apples (reuse base apple logic)
        if new_head in self.apples:
            self.apples.remove(new_head)
            self.apples.append(self.spawn_food())
            self.score += 1

            if self.score > self.highscore:
                self.highscore = self.score
                self.beat_highscore = True
                self.highscores[self.mode] = self.highscore
        else:
            self.snake.pop()

        # Draw
        self.draw()
        self.root.after(self.speed, self.update)

    # Patch method
    import types
    game.update = types.MethodType(ghost_update, game)
