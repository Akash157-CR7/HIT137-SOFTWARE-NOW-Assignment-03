"""
image_processor.py
------------------
Handles all OpenCV and Pillow operations for the game.

OOP concepts shown here:
    Encapsulation  — image data and scale factor are private attributes
    Composition    — owns the alteration pool (list of BaseAlteration objects)
    Polymorphism   — calls alteration.apply() on whichever subclass is chosen
    Single responsibility — no GUI code lives here
"""

from __future__ import annotations
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageTk

from alterations import BaseAlteration, BlurAlteration, BrightnessAlteration, ColourShift, PixelateAlteration
from difference_region import DifferenceRegion

# How many differences to place per round
DIFFERENCE_COUNT = 5

# Maximum canvas size (keeps images comfortable on screen)
MAX_DISPLAY_WIDTH  = 560
MAX_DISPLAY_HEIGHT = 420


class ImageProcessor:
    """
    Loads images from disk, generates hidden differences, and produces
    Tkinter-compatible PhotoImages for the GUI.

    The GUI layer never touches NumPy arrays or OpenCV directly — all of
    that is encapsulated here.
    """

    def __init__(self) -> None:
        # Pool of concrete alteration objects (composition)
        self._alterations: list[BaseAlteration] = [
            ColourShift(),
            BlurAlteration(),
            BrightnessAlteration(),
            PixelateAlteration(),
        ]
        # Cached state set after load_image() is called
        self._original: np.ndarray | None = None
        self._scale:    float             = 1.0

    # ── public interface ──────────────────────────────────────────────────

    def load_image(self, path: str | Path) -> np.ndarray:
        """
        Read an image from *path* using OpenCV.

        Returns the full-resolution BGR array.
        Raises ValueError if the file cannot be opened.
        """
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(
                f"Could not open '{path}'.\n"
                "Please choose a JPG, PNG, or BMP file."
            )
        self._original = img
        self._scale    = self._compute_scale(img.shape)
        return img

    def create_round(
        self, original: np.ndarray
    ) -> tuple[np.ndarray, list[DifferenceRegion]]:
        """
        Build a modified copy of *original* with DIFFERENCE_COUNT differences.

        Steps:
            1. Copy the original so the source is never mutated.
            2. Place DIFFERENCE_COUNT non-overlapping regions randomly.
            3. Apply a randomly chosen alteration to each region
               (polymorphic dispatch: alteration.apply(image, region)).
            4. Return (modified_image, region_list).
        """
        modified = original.copy()
        regions  = self._place_regions(original.shape)

        for region in regions:
            alteration = random.choice(self._alterations)
            region.alteration_name = alteration.label
            alteration.apply(modified, region)   # polymorphism in action

        return modified, regions

    def to_photo_image(self, bgr_image: np.ndarray) -> tuple[ImageTk.PhotoImage, float]:
        """
        Convert a BGR NumPy array to a Tkinter PhotoImage scaled to fit the display.

        Returns (photo_image, scale_factor).
        The GUI uses scale_factor to convert canvas coordinates back to image space.
        """
        scale   = self._compute_scale(bgr_image.shape)
        h, w    = bgr_image.shape[:2]
        disp_w  = max(1, int(w * scale))
        disp_h  = max(1, int(h * scale))

        resized = cv2.resize(bgr_image, (disp_w, disp_h), interpolation=cv2.INTER_AREA)
        rgb     = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        photo   = ImageTk.PhotoImage(Image.fromarray(rgb))
        return photo, scale

    # ── private helpers ───────────────────────────────────────────────────

    def _compute_scale(self, shape: tuple) -> float:
        """Return the uniform scale factor to fit image inside the display limits."""
        h, w = shape[:2]
        return min(MAX_DISPLAY_WIDTH / w, MAX_DISPLAY_HEIGHT / h, 1.0)

    def _place_regions(self, shape: tuple) -> list[DifferenceRegion]:
        """
        Randomly place DIFFERENCE_COUNT non-overlapping DifferenceRegion objects.

        Tries up to 2000 candidates before raising RuntimeError (only happens
        with very small images).
        """
        img_h, img_w = shape[:2]
        min_sz = max(28, int(min(img_w, img_h) * 0.06))
        max_sz = max(min_sz + 10, int(min(img_w, img_h) * 0.12))

        placed:   list[DifferenceRegion] = []
        attempts  = 0

        while len(placed) < DIFFERENCE_COUNT and attempts < 2_000:
            attempts += 1
            rw = random.randint(min_sz, max_sz)
            rh = random.randint(min_sz, max_sz)
            rx = random.randint(0, max(0, img_w - rw - 1))
            ry = random.randint(0, max(0, img_h - rh - 1))

            candidate = DifferenceRegion(rx, ry, rw, rh, "")
            if all(not candidate.overlaps(p) for p in placed):
                placed.append(candidate)

        if len(placed) != DIFFERENCE_COUNT:
            raise RuntimeError(
                "Could not place all five differences without overlap.\n"
                "Try using a larger image."
            )
        return placed
