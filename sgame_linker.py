import os
import subprocess
import sys

# --- Get consistent paths no matter where it's run from ---
# This ensures it works when opened from Windows Search or Explorer
script_dir = os.path.dirname(os.path.abspath(__file__))
snake_path = os.path.join(script_dir, "snake.py")
mods_folder = os.path.join(script_dir, "snakemods")
flag_path = os.path.join(mods_folder, ".launch_flag")

# Make sure snakemods exists
os.makedirs(mods_folder, exist_ok=True)

# --- First-time setup ---
if not os.path.exists(flag_path):
    print("Welcome!")
    print("This file links your search bar and shortcuts/accessories to the game 'snake.py'.")
    print("From this point forward, type 'sgame' into the Windows search bar to open Snake.")
    print("If you do not have the game, you can delete this file.")
    print("You will only see this message once.")
    
    with open(flag_path, "w") as f:
        f.write("launched")
    
    input("\nPress Enter to close...")
    sys.exit(0)

# --- Launch Snake ---
if not os.path.exists(snake_path):
    print("Error: snake.py not found in this directory.")
    input("\nPress Enter to close...")
    sys.exit(1)

print("Launching Snake...")
subprocess.run([sys.executable, snake_path], cwd=script_dir)
