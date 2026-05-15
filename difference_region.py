"""
difference_region.py
--------------------
Defines DifferenceRegion — the core data object for one hidden difference.

OOP concepts shown here:
    Encapsulation  — all position/state fields live in one class
    Data modelling — Python dataclass generates __init__ and __repr__
    Methods        — contains_click() and overlaps() keep logic together
"""

from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass
class DifferenceRegion:
    """
    One hidden difference between the original and modified images.

    Fields
    ------
    x, y            : top-left corner in original-image pixels
    width, height   : region size in pixels
    alteration_name : label of the alteration applied (e.g. "Blur")
    found           : True after the player clicks this region
    revealed        : True if the player presses Reveal first
    """

    x: int
    y: int
    width: int
    height: int
    alteration_name: str
    found: bool = False
    revealed: bool = False

    @property
    def centre(self) -> tuple[int, int]:
        """Return the (cx, cy) centre of this region."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def hit_radius(self) -> int:
        """
        Click-detection radius: half the longer dimension plus 12 px margin.
        A circular hit zone feels more natural than a strict rectangle.
        """
        return max(self.width, self.height) // 2 + 12

    def contains_click(self, click_x: int, click_y: int) -> bool:
        """Return True if the click lands within this region's hit circle."""
        cx, cy = self.centre
        return math.hypot(click_x - cx, click_y - cy) <= self.hit_radius

    def overlaps(self, other: "DifferenceRegion", gap: int = 20) -> bool:
        """
        Return True if this region and *other* are too close together.

        The *gap* argument adds a minimum pixel buffer so differences are
        never placed right next to each other.
        """
        return not (
            self.x + self.width  + gap <= other.x
            or other.x + other.width  + gap <= self.x
            or self.y + self.height + gap <= other.y
            or other.y + other.height + gap <= self.y
        )
