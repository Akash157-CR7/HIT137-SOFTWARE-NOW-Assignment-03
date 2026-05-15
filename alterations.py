"""
GROUP DAN/EXT 32:

•	ANGEL SHAHI         (s400420)
•	ANJIT SHRESTHA      (s400533)
•	AKASH SINGH         (s401643)
•	DANIEL HARTREE      (s394765)

alterations.py
--------------
All image-alteration logic for the game.

OOP concepts shown here:
    Abstraction   — BaseAlteration declares apply() as abstract (ABC)
    Inheritance   — four concrete classes all extend BaseAlteration
    Polymorphism  — ImageProcessor calls alteration.apply(img, region)
                    and the correct child method runs automatically
    Encapsulation — each class hides its tuning constants privately
"""

from __future__ import annotations
import random
from abc import ABC, abstractmethod

import cv2
import numpy as np

# Forward reference only (avoids circular import at runtime)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from difference_region import DifferenceRegion


# ─────────────────────────────────────────────────────────────────────────────
# Abstract base class
# ─────────────────────────────────────────────────────────────────────────────

class BaseAlteration(ABC):
    """
    Abstract base for every alteration type.

    Subclasses must implement apply().  The class-level attribute `label`
    gives the alteration a human-readable name that is stored on each
    DifferenceRegion and shown to the player when they find a difference.
    """

    label: str = "Unknown"

    @abstractmethod
    def apply(self, image: np.ndarray, region: "DifferenceRegion") -> None:
        """
        Modify *image* in-place within the area defined by *region*.

        Parameters
        ----------
        image  : full BGR image as a NumPy array (modified in-place)
        region : defines the rectangular patch to alter
        """

    # Shared helper — all subclasses use this to extract the patch slice
    def _slice(self, image: np.ndarray, region: "DifferenceRegion") -> np.ndarray:
        """Return a view into the image at the region's bounding box."""
        return image[region.y : region.y + region.height,
                     region.x : region.x + region.width]


# ─────────────────────────────────────────────────────────────────────────────
# Concrete alteration subclasses
# ─────────────────────────────────────────────────────────────────────────────

class ColourShift(BaseAlteration):
    """
    Alteration 1 — Colour Shift.

    Nudges the hue channel in HSV space by a small random amount.
    The change is noticeable on close inspection but not immediately obvious.
    """

    label = "Colour Shift"
    _MIN_SHIFT = 12   # degrees (OpenCV hue range is 0–179)
    _MAX_SHIFT = 28

    def apply(self, image: np.ndarray, region: "DifferenceRegion") -> None:
        patch = self._slice(image, region).copy()
        hsv   = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)

        shift = random.randint(self._MIN_SHIFT, self._MAX_SHIFT)
        hsv[:, :, 0] = (hsv[:, :, 0].astype(np.int16) + shift) % 180

        image[region.y : region.y + region.height,
              region.x : region.x + region.width] = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


class BlurAlteration(BaseAlteration):
    """
    Alteration 2 — Gaussian Blur.

    Blends the original patch with a blurred copy (60/40 mix) so the
    softening is subtle enough to require careful inspection.
    """

    label = "Blur"
    _SIGMA = 2.5

    def apply(self, image: np.ndarray, region: "DifferenceRegion") -> None:
        patch   = self._slice(image, region)
        blurred = cv2.GaussianBlur(patch, (0, 0), sigmaX=self._SIGMA)

        image[region.y : region.y + region.height,
              region.x : region.x + region.width] = cv2.addWeighted(
            patch, 0.40, blurred, 0.60, 0
        )


class BrightnessAlteration(BaseAlteration):
    """
    Alteration 3 — Brightness Change.

    Adds a fixed offset to every pixel in the region.
    Four discrete levels (±18, ±26) keep changes visible but not glaring.
    """

    label = "Brightness"
    _LEVELS = (-26, -18, 18, 26)

    def apply(self, image: np.ndarray, region: "DifferenceRegion") -> None:
        patch = self._slice(image, region)
        delta = random.choice(self._LEVELS)

        image[region.y : region.y + region.height,
              region.x : region.x + region.width] = np.clip(
            patch.astype(np.int16) + delta, 0, 255
        ).astype(np.uint8)


class PixelateAlteration(BaseAlteration):
    """
    Alteration 4 — Pixelation.

    Shrinks the patch to a tiny size then upscales with nearest-neighbour
    interpolation to create a blocky mosaic effect.
    """

    label = "Pixelate"
    _BLOCK = 8   # mosaic block size in pixels

    def apply(self, image: np.ndarray, region: "DifferenceRegion") -> None:
        patch = self._slice(image, region)
        h, w  = patch.shape[:2]

        small = cv2.resize(patch,
                           (max(1, w // self._BLOCK), max(1, h // self._BLOCK)),
                           interpolation=cv2.INTER_LINEAR)
        mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

        image[region.y : region.y + region.height,
              region.x : region.x + region.width] = mosaic
