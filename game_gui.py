"""
game_gui.py
-----------
Complete Tkinter GUI for the Find the Difference game.

OOP concepts shown here:
    Encapsulation  — all widgets and state are private attributes
    Composition    — owns GameState and ImageProcessor objects
    Class interaction — delegates logic to GameState, images to ImageProcessor
    Single responsibility — no OpenCV or game logic lives here

    
"""

from __future__ import annotations
import time
import tkinter as tk
from tkinter import filedialog, messagebox, font as tkfont
from typing import Optional

from PIL import ImageTk

from game_state import GameState, MAX_MISTAKES
from image_processor import DIFFERENCE_COUNT, MAX_DISPLAY_HEIGHT, MAX_DISPLAY_WIDTH, ImageProcessor


# ── Colour palette ────────────────────────────────────────────────────────────
# Primary accent: teal #2ec4b6 — distinctive and rarely used in academic work.
BG_DARK      = "#1e1e2e"   # main window background
BG_PANEL     = "#252538"   # header / footer panels
BG_CANVAS    = "#16162a"   # empty canvas background

TEAL         = "#2ec4b6"   # primary accent (teal)
TEAL_DARK    = "#1a8a80"   # darker teal for pressed/hover
TEAL_DIM     = "#1d6e68"   # muted teal for disabled borders

BTN_NORMAL   = "#2a2a42"   # button rest background
BTN_HOVER    = "#2ec4b6"   # button hover background (teal flash)
BTN_DISABLED = "#252535"   # button disabled background
BTN_FG       = "#e8f4f3"   # button text (normal)
BTN_FG_DIS   = "#4a5568"   # button text (disabled — visibly muted)

TEXT_PRIMARY  = "#e8f4f3"
TEXT_DIM      = "#7a8aaa"
RED_MARK      = "#ff4f6a"
BLUE_MARK     = "#4fb3ff"
GREEN_FOUND   = "#4fffa0"
YELLOW_WARN   = "#ffd166"


class GameGUI:
    """
    Main application window for the Find the Difference game.

    Responsibilities:
        - Build and own all Tkinter widgets.
        - Respond to user events (button clicks, canvas clicks).
        - Update the display by calling ImageProcessor and GameState.
        - Run the countdown / elapsed timer loop.
    """

    TIMER_INTERVAL_MS = 1_000   # update timer every second

    def __init__(self, root: tk.Tk) -> None:
        # ── root window ───────────────────────────────────────────────────
        self._root = root
        self._root.title("Find the Difference")
        self._root.configure(bg=BG_DARK)
        self._root.resizable(True, True)
        self._root.minsize(1000, 640)

        # ── backend objects (composition) ─────────────────────────────────
        self._processor = ImageProcessor()
        self._state     = GameState()

        # ── image cache (must keep references to prevent GC) ──────────────
        self._orig_photo:  Optional[ImageTk.PhotoImage] = None
        self._mod_photo:   Optional[ImageTk.PhotoImage] = None
        self._orig_image   = None   # np.ndarray
        self._mod_image    = None   # np.ndarray
        self._scale:       float    = 1.0
        self._img_offset:  tuple[int, int] = (0, 0)

        # ── timer state ───────────────────────────────────────────────────
        self._start_time:  Optional[float] = None
        self._elapsed_sec: int = 0
        self._timer_running = False

        # ── build UI ──────────────────────────────────────────────────────
        self._build_header()
        self._build_toolbar()
        self._build_canvas_area()
        self._build_footer()
        self._refresh_counters()

    # =========================================================================
    # UI construction
    # =========================================================================

    def _build_header(self) -> None:
        """Top bar: game title, total score, and elapsed timer."""
        header = tk.Frame(self._root, bg=BG_PANEL, pady=14)
        header.pack(fill=tk.X)

        title_font = tkfont.Font(family="Segoe UI", size=20, weight="bold")
        info_font  = tkfont.Font(family="Segoe UI", size=13)

        tk.Label(header, text="🔍  Find the Difference",
                 font=title_font, fg=TEXT_PRIMARY, bg=BG_PANEL
                 ).pack(side=tk.LEFT, padx=24)

        # Right-side info: score + timer
        right = tk.Frame(header, bg=BG_PANEL)
        right.pack(side=tk.RIGHT, padx=24)

        self._score_var = tk.StringVar(value="Total found: 0")
        self._timer_var = tk.StringVar(value="⏱  0:00")

        tk.Label(right, textvariable=self._score_var,
                 font=info_font, fg=GREEN_FOUND, bg=BG_PANEL
                 ).pack(side=tk.LEFT, padx=16)
        tk.Label(right, textvariable=self._timer_var,
                 font=info_font, fg=YELLOW_WARN, bg=BG_PANEL
                 ).pack(side=tk.LEFT, padx=8)

    def _build_toolbar(self) -> None:
        """Button row + status message."""
        bar = tk.Frame(self._root, bg=BG_PANEL, pady=10)
        bar.pack(fill=tk.X, padx=20)

        btn_font = tkfont.Font(family="Segoe UI", size=11, weight="bold")

        self._btn_load    = self._make_button(bar, "📂  Load Image", self._on_load,    btn_font)
        self._btn_reveal  = self._make_button(bar, "👁  Reveal",     self._on_reveal,  btn_font, state=tk.DISABLED)
        self._btn_restart = self._make_button(bar, "🔄  Restart",    self._on_restart, btn_font, state=tk.DISABLED)

        self._btn_load.pack(side=tk.LEFT, padx=(0, 8))
        self._btn_reveal.pack(side=tk.LEFT, padx=8)
        self._btn_restart.pack(side=tk.LEFT, padx=8)

        # Status message on the right
        self._status_var = tk.StringVar(value="Load an image to start playing.")
        tk.Label(bar, textvariable=self._status_var,
                 font=tkfont.Font(family="Segoe UI", size=11),
                 fg=TEXT_DIM, bg=BG_PANEL, anchor="w"
                 ).pack(side=tk.LEFT, padx=20)

    def _make_button(self, parent, text: str, command, btn_font,
                     state=tk.NORMAL) -> tk.Button:
        """
        Factory: create a solid, always-visible styled button.

        Normal state  : dark navy fill, teal-white text
        Hover         : teal fill (clearly different from rest)
        Disabled state: visibly muted — dark bg + greyed text so it is
                        obvious the button is inactive without being invisible
        """
        is_normal   = (state == tk.NORMAL)
        initial_bg  = BTN_NORMAL if is_normal else BTN_DISABLED
        initial_fg  = BTN_FG    if is_normal else BTN_FG_DIS

        btn = tk.Button(
            parent, text=text, command=command,
            font=btn_font,
            bg=initial_bg, fg=initial_fg,
            activebackground=TEAL_DARK, activeforeground=TEXT_PRIMARY,
            disabledforeground=BTN_FG_DIS,  # explicit: no OS override
            relief=tk.FLAT,
            padx=16, pady=8,
            cursor="hand2",
            state=state,
            bd=0,
            highlightthickness=1,
            highlightbackground=TEAL_DIM,
            highlightcolor=TEAL,
        )

        def on_enter(e):
            if btn["state"] == tk.NORMAL:
                btn.config(bg=BTN_HOVER, fg="#0d2020")

        def on_leave(e):
            if btn["state"] == tk.NORMAL:
                btn.config(bg=BTN_NORMAL, fg=BTN_FG)
            else:
                btn.config(bg=BTN_DISABLED, fg=BTN_FG_DIS)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def _set_button_state(self, btn: tk.Button, state: str) -> None:
        """Enable or disable a button and update its colours consistently."""
        btn.config(state=state)
        if state == tk.NORMAL:
            btn.config(bg=BTN_NORMAL, fg=BTN_FG)
        else:
            btn.config(bg=BTN_DISABLED, fg=BTN_FG_DIS)

    def _build_canvas_area(self) -> None:
        """Side-by-side canvas area for original and modified images."""
        label_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")

        # Outer wrapper — just centres the pair horizontally
        outer = tk.Frame(self._root, bg=BG_DARK)
        outer.pack(fill=tk.X, padx=20, pady=(0, 6))

        # Left column: label + canvas
        left_col = tk.Frame(outer, bg=BG_DARK)
        left_col.pack(side=tk.LEFT, expand=True)

        tk.Label(left_col, text="Original  (reference)",
                 font=label_font, fg=TEXT_DIM, bg=BG_DARK
                 ).pack(pady=(6, 3))

        self._canvas_orig = tk.Canvas(
            left_col,
            bg=BG_CANVAS,
            width=MAX_DISPLAY_WIDTH,
            height=MAX_DISPLAY_HEIGHT,
            highlightthickness=1,
            highlightbackground=TEAL_DIM,
            cursor="arrow",
        )
        self._canvas_orig.pack()

        # Right column: label + canvas (teal border = clickable)
        right_col = tk.Frame(outer, bg=BG_DARK)
        right_col.pack(side=tk.LEFT, expand=True)

        tk.Label(right_col, text="Modified  —  click here to find differences",
                 font=label_font, fg=TEAL, bg=BG_DARK
                 ).pack(pady=(6, 3))

        self._canvas_mod = tk.Canvas(
            right_col,
            bg=BG_CANVAS,
            width=MAX_DISPLAY_WIDTH,
            height=MAX_DISPLAY_HEIGHT,
            highlightthickness=2,
            highlightbackground=TEAL,
            cursor="crosshair",
        )
        self._canvas_mod.pack()

        self._canvas_mod.bind("<Button-1>", self._on_canvas_click)

    def _build_footer(self) -> None:
        """Bottom status bar: remaining · mistakes · hint."""
        footer = tk.Frame(self._root, bg=BG_PANEL, pady=10)
        footer.pack(fill=tk.X)

        stat_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        hint_font = tkfont.Font(family="Segoe UI", size=10)

        self._remaining_var = tk.StringVar(value="Remaining: —")
        self._mistakes_var  = tk.StringVar(value="Mistakes: 0 / 3")

        tk.Label(footer, textvariable=self._remaining_var,
                 font=stat_font, fg=GREEN_FOUND, bg=BG_PANEL
                 ).pack(side=tk.LEFT, padx=24)

        tk.Label(footer, textvariable=self._mistakes_var,
                 font=stat_font, fg=RED_MARK, bg=BG_PANEL
                 ).pack(side=tk.LEFT, padx=16)

        tk.Label(footer,
                 text="Tip: differences are subtle — look carefully.",
                 font=hint_font, fg=TEXT_DIM, bg=BG_PANEL
                 ).pack(side=tk.RIGHT, padx=24)

    # =========================================================================
    # Event handlers
    # =========================================================================

    def _on_load(self) -> None:
        """Load Image button — open file dialog and start a new round."""
        path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.JPG *.PNG"),
                ("All files",   "*.*"),
            ],
        )
        if not path:
            return

        try:
            original          = self._processor.load_image(path)
            modified, regions = self._processor.create_round(original)
        except Exception as err:
            messagebox.showerror("Could not load image", str(err))
            return

        self._orig_image = original
        self._mod_image  = modified
        self._state.start_round(regions)

        self._set_button_state(self._btn_reveal,  tk.NORMAL)
        self._set_button_state(self._btn_restart, tk.NORMAL)
        self._canvas_mod.config(cursor="crosshair")

        self._draw_images()
        self._refresh_counters()
        self._set_status("Round started — find all 5 differences!")
        self._start_timer()

    def _on_canvas_click(self, event: tk.Event) -> None:
        """Handle a click on the modified image canvas."""
        if self._mod_image is None or self._state.locked:
            return

        img_x, img_y = self._canvas_to_image(event.x, event.y)
        if img_x is None:
            return   # outside image bounds

        hit = self._state.register_click(img_x, img_y)

        if hit is not None:
            # ── correct click ─────────────────────────────────────────────
            self._draw_marker(hit, RED_MARK)
            self._set_status(f"✅  Found: {hit.alteration_name}!")
            self._refresh_counters()

            if self._state.locked:   # all found
                self._stop_timer()
                self._canvas_mod.config(cursor="arrow")
                elapsed = self._format_time(self._elapsed_sec)
                messagebox.showinfo(
                    "🎉  You win!",
                    f"All {DIFFERENCE_COUNT} differences found!\n\n"
                    f"Mistakes:  {self._state.mistakes}\n"
                    f"Time:      {elapsed}\n"
                    f"Total score: {self._state.total_found}",
                )
        else:
            # ── wrong click ───────────────────────────────────────────────
            self._flash_wrong(event.x, event.y)
            self._set_status(f"❌  Not quite. Mistakes: {self._state.mistakes} / {MAX_MISTAKES}")
            self._refresh_counters()

            if self._state.locked:   # too many mistakes
                self._stop_timer()
                self._canvas_mod.config(cursor="arrow")
                messagebox.showwarning(
                    "Round over",
                    f"Too many mistakes ({MAX_MISTAKES}).\n\n"
                    f"You found {self._state.found_this_round} of "
                    f"{DIFFERENCE_COUNT} differences.\n\n"
                    "Press Reveal to see the answers, or Load Image to try again.",
                )

    def _on_reveal(self) -> None:
        """Reveal button — show all unfound differences in blue."""
        if not self._state.regions:
            return
        self._stop_timer()
        revealed = self._state.reveal_all()
        for region in revealed:
            self._draw_marker(region, BLUE_MARK)
        self._canvas_mod.config(cursor="arrow")
        self._refresh_counters()
        self._set_status(
            f"Revealed. You found {self._state.found_this_round} / {DIFFERENCE_COUNT}."
        )

    def _on_restart(self) -> None:
        """Restart button — reload the same image with fresh differences."""
        if self._orig_image is None:
            return
        try:
            modified, regions = self._processor.create_round(self._orig_image)
        except Exception as err:
            messagebox.showerror("Error", str(err))
            return

        self._mod_image = modified
        self._state.start_round(regions)
        self._canvas_mod.config(cursor="crosshair")
        self._draw_images()
        self._refresh_counters()
        self._set_status("New round — find all 5 differences!")
        self._start_timer()

    # =========================================================================
    # Timer helpers
    # =========================================================================

    def _start_timer(self) -> None:
        """Reset and start the elapsed-time counter."""
        self._start_time   = time.monotonic()
        self._elapsed_sec  = 0
        self._timer_running = True
        self._tick()

    def _stop_timer(self) -> None:
        self._timer_running = False

    def _tick(self) -> None:
        """Called every second to update the timer label."""
        if not self._timer_running:
            return
        self._elapsed_sec = int(time.monotonic() - self._start_time)
        self._timer_var.set(f"⏱  {self._format_time(self._elapsed_sec)}")
        self._root.after(self.TIMER_INTERVAL_MS, self._tick)

    @staticmethod
    def _format_time(seconds: int) -> str:
        return f"{seconds // 60}:{seconds % 60:02d}"

    # =========================================================================
    # Display helpers
    # =========================================================================

    def _draw_images(self) -> None:
        """Scale and display both images on their respective canvases."""
        if self._orig_image is None or self._mod_image is None:
            return

        orig_photo, self._scale = self._processor.to_photo_image(self._orig_image)
        mod_photo,  _           = self._processor.to_photo_image(self._mod_image)

        # Compute centering offset so the image sits in the middle of the canvas
        disp_w = int(self._orig_image.shape[1] * self._scale)
        disp_h = int(self._orig_image.shape[0] * self._scale)
        off_x  = (MAX_DISPLAY_WIDTH  - disp_w) // 2
        off_y  = (MAX_DISPLAY_HEIGHT - disp_h) // 2
        self._img_offset = (off_x, off_y)

        # Keep strong references — without these Tkinter shows a blank canvas
        self._orig_photo = orig_photo
        self._mod_photo  = mod_photo

        for canvas, photo in ((self._canvas_orig, orig_photo),
                               (self._canvas_mod,  mod_photo)):
            canvas.delete("all")
            canvas.create_image(off_x, off_y, image=photo, anchor=tk.NW)

    def _draw_marker(self, region, colour: str, tag: str = "") -> None:
        """Draw a coloured oval around *region* on both canvases."""
        cx, cy = region.centre
        r      = max(region.width, region.height) // 2 + 8
        ox, oy = self._img_offset
        s      = self._scale

        x1 = ox + int((cx - r) * s)
        y1 = oy + int((cy - r) * s)
        x2 = ox + int((cx + r) * s)
        y2 = oy + int((cy + r) * s)

        opts = dict(outline=colour, width=3)
        self._canvas_orig.create_oval(x1, y1, x2, y2, **opts)
        self._canvas_mod.create_oval( x1, y1, x2, y2, **opts)

    def _flash_wrong(self, cx: int, cy: int) -> None:
        """Draw a small red X on the modified canvas where the player missed."""
        size = 10
        tag  = "flash"
        self._canvas_mod.create_line(cx - size, cy - size, cx + size, cy + size,
                                      fill=RED_MARK, width=2, tags=tag)
        self._canvas_mod.create_line(cx + size, cy - size, cx - size, cy + size,
                                      fill=RED_MARK, width=2, tags=tag)
        # Remove the X after 600 ms
        self._root.after(600, lambda: self._canvas_mod.delete(tag))

    def _canvas_to_image(self, cx: int, cy: int) -> tuple[int | None, int | None]:
        """
        Convert a canvas pixel coordinate to original-image pixel coordinates.

        Returns (None, None) if the click is outside the image bounds.
        """
        if self._mod_image is None:
            return None, None
        ox, oy = self._img_offset
        img_x  = int((cx - ox) / self._scale)
        img_y  = int((cy - oy) / self._scale)
        h, w   = self._mod_image.shape[:2]
        if img_x < 0 or img_y < 0 or img_x >= w or img_y >= h:
            return None, None
        return img_x, img_y

    def _refresh_counters(self) -> None:
        """Sync all counter labels with current GameState values."""
        rem = self._state.remaining if self._state.regions else 0
        self._remaining_var.set(
            f"Remaining: {rem}" if self._state.regions else "Remaining: —"
        )
        self._mistakes_var.set(
            f"Mistakes: {self._state.mistakes} / {MAX_MISTAKES}"
        )
        self._score_var.set(f"Total found: {self._state.total_found}")

    def _set_status(self, message: str) -> None:
        """Update the toolbar status message."""
        self._status_var.set(message)
