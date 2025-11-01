mod_name = "Triple Growth Mode"
mod_version = "2.0"
mod_description = "Each apple increases your snake length by 3 instead of 1."

import types

def on_menu_open(root, canvas, options, modes, grids, submenus):
    """Add Triple Growth mode to the mode list."""
    if "Triple Growth" not in modes:
        modes.append("Triple Growth")


def on_game_start(game):
    """Patch the update method so apples grow by 3."""
    if getattr(game, "mode", "") != "Triple Growth":
        return  # Only patch if in this mode

    original_update = game.update

    def triple_update(self):
        """Wrapped update function that grows 3 segments on apple collision."""
        if not self.running:
            return

        # Save old snake before movement
        prev_snake = list(self.snake)

        # Run one frame of the original update
        original_update()

        # Check if a new apple was eaten
        if hasattr(self, "score") and hasattr(self, "snake"):
            # Detect if the snake grew this frame
            if len(self.snake) > len(prev_snake):
                # Add 2 extra segments (total +3 growth)
                tail = self.snake[-1]
                for _ in range(2):  # +2 because base already added +1
                    self.snake.append(tail)

    # Patch game.update only once
    game.update = types.MethodType(triple_update, game)
