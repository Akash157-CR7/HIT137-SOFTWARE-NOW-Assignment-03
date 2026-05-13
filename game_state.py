"""
game_state.py
-------------
Manages the full lifecycle of one game round.

OOP concepts shown here:
    Encapsulation  — private counters exposed through read-only properties
    Composition    — owns a list of DifferenceRegion objects
    Single responsibility — no GUI or OpenCV code lives here

Public API used by the GUI
--------------------------
    state.start_round(regions)          — begin a new round
    state.register_click(x, y)         — process a player click
    state.reveal_all()                  — reveal every unfound region
    state.remaining                     — property: unfound count
    state.mistakes                      — property: wrong-click count
    state.total_found                   — property: cumulative score
    state.locked                        — property: True when round is over
    state.regions                       — property: current region list
"""

from __future__ import annotations
from typing import Optional

from difference_region import DifferenceRegion
from image_processor import DIFFERENCE_COUNT

MAX_MISTAKES = 3


class GameState:
    """
    Tracks round state: clicks, mistakes, score, and locked status.

    A "locked" round means no more clicks are accepted — this happens
    either when all differences are found or MAX_MISTAKES is reached.
    """

    def __init__(self) -> None:
        self._regions:      list[DifferenceRegion] = []
        self._mistakes:     int  = 0
        self._total_found:  int  = 0   # cumulative across all rounds
        self._locked:       bool = True  # locked until start_round() is called

    # ── public methods ────────────────────────────────────────────────────

    def start_round(self, regions: list[DifferenceRegion]) -> None:
        """
        Start a new round with the given regions.

        Resets per-round counters (mistakes, locked) but keeps total_found
        so the cumulative score carries over between images.
        """
        self._regions  = regions
        self._mistakes = 0
        self._locked   = False

    def register_click(self, img_x: int, img_y: int) -> Optional[DifferenceRegion]:
        """
        Process a click at image-space coordinates (img_x, img_y).

        Returns the matched DifferenceRegion on a hit, or None on a miss.
        Increments mistakes and potentially locks the round on a miss.
        """
        if self._locked:
            return None

        # Check each unfound, unrevealed region
        for region in self._regions:
            if not region.found and not region.revealed:
                if region.contains_click(img_x, img_y):
                    region.found    = True
                    self._total_found += 1
                    # Lock if all differences are found
                    if self.remaining == 0:
                        self._locked = True
                    return region

        # Miss
        self._mistakes += 1
        if self._mistakes >= MAX_MISTAKES:
            self._locked = True
        return None

    def reveal_all(self) -> list[DifferenceRegion]:
        """
        Mark every unfound region as revealed and lock the round.

        Returns the list of newly revealed regions so the GUI can
        draw blue markers over them.
        """
        newly_revealed = []
        for region in self._regions:
            if not region.found and not region.revealed:
                region.revealed = True
                newly_revealed.append(region)
        self._locked = True
        return newly_revealed

    # ── read-only properties ──────────────────────────────────────────────

    @property
    def regions(self) -> list[DifferenceRegion]:
        """Current round's region list."""
        return self._regions

    @property
    def remaining(self) -> int:
        """Number of differences the player still needs to find."""
        return sum(1 for r in self._regions if not r.found and not r.revealed)

    @property
    def found_this_round(self) -> int:
        """Differences found so far this round."""
        return sum(1 for r in self._regions if r.found)

    @property
    def mistakes(self) -> int:
        """Wrong clicks made this round."""
        return self._mistakes

    @property
    def total_found(self) -> int:
        """Cumulative differences found across all rounds."""
        return self._total_found

    @property
    def locked(self) -> bool:
        """True when no more clicks should be accepted."""
        return self._locked

    @property
    def max_mistakes(self) -> int:
        """Maximum mistakes allowed per round (read from module constant)."""
        return MAX_MISTAKES