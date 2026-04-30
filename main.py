import tkinter as tk
from gui import GameGUI


# This is the main file.
# It starts the Tkinter window and runs the game.
def main():
    # Create the main Tkinter window
    root = tk.Tk()

    # Create the game GUI inside the window
    app = GameGUI(root)

    # Keep the window open until the user closes it
    root.mainloop()


# This means the program will start from here
# when we run main.py
if __name__ == "__main__":
    main()