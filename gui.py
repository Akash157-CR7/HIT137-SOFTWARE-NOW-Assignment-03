import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
from PIL import Image, ImageTk

from image_processor import ImageProcessor
from game import DifferenceGame


class GameGUI:
    """
    This class creates the game window using Tkinter.

    It shows the original image on the left and the modified image
    on the right. The player clicks the modified image to find differences.
    """

    def __init__(self, root):
        # Store the main Tkinter window
        self.root = root
        self.root.title("Spot the Difference Game")

        # Create objects from our other classes
        self.image_processor = ImageProcessor()
        self.game = DifferenceGame()

        # These variables will store image data
        self.original_image = None
        self.modified_image = None

        # These two images are the copies shown on screen.
        # We draw circles on these copies, not on the original stored images.
        self.display_original_image = None
        self.display_modified_image = None

        # These values help convert the click position correctly
        # if the image is resized for display.
        self.scale_x = 1
        self.scale_y = 1

        # Create the buttons, labels, and image areas
        self.create_widgets()

    def create_widgets(self):
        """
        This method creates all the buttons, labels, and image areas.
        """

        # Title label
        title_label = tk.Label(
            self.root,
            text="Spot the Difference Game",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=10)

        # Frame for buttons and game information
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5)

        # Button to choose an image
        load_button = tk.Button(
            top_frame,
            text="Load Image",
            command=self.load_image
        )
        load_button.grid(row=0, column=0, padx=10)

        # Button to reveal the remaining differences
        reveal_button = tk.Button(
            top_frame,
            text="Reveal Differences",
            command=self.reveal_differences
        )
        reveal_button.grid(row=0, column=1, padx=10)

        # Label to show remaining differences
        self.remaining_label = tk.Label(
            top_frame,
            text="Remaining: 5",
            font=("Arial", 12)
        )
        self.remaining_label.grid(row=0, column=2, padx=10)

        # Label to show mistake count
        self.mistake_label = tk.Label(
            top_frame,
            text="Mistakes: 0/3",
            font=("Arial", 12)
        )
        self.mistake_label.grid(row=0, column=3, padx=10)

        # Frame for displaying the two images
        image_frame = tk.Frame(self.root)
        image_frame.pack(pady=10)

        # Label above original image
        original_text = tk.Label(image_frame, text="Original Image")
        original_text.grid(row=0, column=0)

        # Label above modified image
        modified_text = tk.Label(image_frame, text="Modified Image")
        modified_text.grid(row=0, column=1)

        # This label will show the original image
        self.original_label = tk.Label(image_frame)
        self.original_label.grid(row=1, column=0, padx=10)

        # This label will show the modified image
        self.modified_label = tk.Label(image_frame)
        self.modified_label.grid(row=1, column=1, padx=10)

        # Only the modified image should respond to player clicks
        self.modified_label.bind("<Button-1>", self.handle_click)

    def load_image(self):
        """
        This method lets the user choose an image from the computer.
        """

        # Open a file picker so the user can choose an image
        image_path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*")
            ]
        )

        # If the user closes the file picker without choosing an image
        if not image_path:
            return

        try:
            # Load the original image using OpenCV
            self.original_image = self.image_processor.load_image(image_path)

            # Create a modified version with 5 random differences
            self.modified_image, difference_regions = self.image_processor.create_modified_image(
                self.original_image
            )

            # Start a new game using the 5 difference areas
            self.game.start_new_game(difference_regions)

            # Make display copies of both images.
            # Circles will be drawn on these copies.
            self.display_original_image = self.original_image.copy()
            self.display_modified_image = self.modified_image.copy()

            # Show both images in the window
            self.show_images()

            # Update the remaining and mistake labels
            self.update_status_labels()

        except Exception as error:
            messagebox.showerror("Error", str(error))

    def show_images(self):
        """
        This method displays the original and modified images in Tkinter.
        """

        # Convert the original image to a Tkinter-friendly image
        original_tk_image = self.convert_cv_image_to_tk(self.display_original_image)

        # Convert the modified image to a Tkinter-friendly image
        modified_tk_image = self.convert_cv_image_to_tk(self.display_modified_image)

        # Keep references so the images do not disappear
        self.original_label.image = original_tk_image
        self.modified_label.image = modified_tk_image

        # Show the images in the labels
        self.original_label.config(image=original_tk_image)
        self.modified_label.config(image=modified_tk_image)

    def convert_cv_image_to_tk(self, cv_image):
        """
        This method converts an OpenCV image into a Tkinter image.

        OpenCV uses BGR colour format.
        Tkinter and Pillow use RGB colour format.
        """

        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)

        # Convert OpenCV image to Pillow image
        pillow_image = Image.fromarray(rgb_image)

        # Resize the image so it fits nicely in the window
        max_width = 450
        max_height = 350

        original_width, original_height = pillow_image.size

        width_ratio = max_width / original_width
        height_ratio = max_height / original_height

        # Use the smaller scale so the image fits inside both limits
        scale = min(width_ratio, height_ratio, 1)

        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        # Store scale values so click positions can be converted correctly
        self.scale_x = original_width / new_width
        self.scale_y = original_height / new_height

        # Resize the image
        pillow_image = pillow_image.resize((new_width, new_height))

        # Convert Pillow image to Tkinter image
        tk_image = ImageTk.PhotoImage(pillow_image)

        return tk_image

    def handle_click(self, event):
        """
        This method runs when the player clicks the modified image.
        """

        # If no image is loaded, ignore the click
        if self.modified_image is None:
            return

        # Convert displayed click position back to original image position
        click_x = int(event.x * self.scale_x)
        click_y = int(event.y * self.scale_y)

        # Check if the click is correct, wrong, already found, or game over
        result, region = self.game.check_click(click_x, click_y)

        if result == "correct":
            # Draw a red circle around the found difference on both images
            self.draw_circle(region, colour=(0, 0, 255))
            messagebox.showinfo("Correct", "You found a difference!")

        elif result == "already_found":
            messagebox.showinfo("Already Found", "You already found this difference.")

        elif result == "wrong":
            messagebox.showwarning("Wrong", "That is not a difference.")

        elif result == "game_over":
            messagebox.showerror(
                "Game Over",
                "You made 3 mistakes. Game over for this image."
            )

        # Update labels after every click
        self.update_status_labels()

        # If all differences are found, show a success message
        if self.game.is_completed():
            messagebox.showinfo("Well Done", "You found all 5 differences!")

    def draw_circle(self, region, colour):
        """
        This method draws a circle around a difference area.

        The circle is drawn on both the original image and the modified image
        because the assignment asks us to mark both images.
        """

        x, y, width, height = region

        # Find the centre of the difference area
        center_x = x + width // 2
        center_y = y + height // 2

        # Use the bigger value as the circle radius
        radius = max(width, height) // 2 + 10

        # Draw circle on the original display image
        cv2.circle(
            self.display_original_image,
            (center_x, center_y),
            radius,
            colour,
            3
        )

        # Draw circle on the modified display image
        cv2.circle(
            self.display_modified_image,
            (center_x, center_y),
            radius,
            colour,
            3
        )

        # Refresh both images on screen
        self.show_images()

    def reveal_differences(self):
        """
        This method reveals all differences that are not found yet.
        """

        # If no image is loaded, show a message
        if self.modified_image is None:
            messagebox.showwarning("No Image", "Please load an image first.")
            return

        # Get all differences that have not been found yet
        unfound_regions = self.game.get_unfound_regions()

        # Draw blue circles around all unfound differences
        for region in unfound_regions:
            self.draw_circle(region, colour=(255, 0, 0))

        messagebox.showinfo("Revealed", "Unfound differences have been revealed.")

    def update_status_labels(self):
        """
        This method updates the remaining and mistake labels.
        """

        remaining = self.game.get_remaining_count()
        mistakes = self.game.get_mistake_count()

        self.remaining_label.config(text=f"Remaining: {remaining}")
        self.mistake_label.config(text=f"Mistakes: {mistakes}/3")