"""
main.py
-------
Entry point — run this file to launch the game.

    python main.py

Project structure
-----------------
    main.py              — entry point (this file)
    game_gui.py          — Tkinter GUI (Member 4)
    game_state.py        — round lifecycle and click logic (Member 3)
    image_processor.py   — OpenCV pipeline (Member 3)
    alterations.py       — alteration class hierarchy (Member 1)
    difference_region.py — data model for one difference (Member 2)

Install dependencies
--------------------
    pip install opencv-python pillow numpy
"""

import tkinter as tk
from game_gui import GameGUI


def main() -> None:
    root = tk.Tk()
    GameGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()