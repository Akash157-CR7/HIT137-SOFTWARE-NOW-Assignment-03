# HIT137 — Find the Difference Game

A desktop "spot the difference" game built with **Python**, **Tkinter**, **OpenCV**, and **Pillow**.  
Load any photo, find 5 hidden differences before running out of mistakes, and track your score across rounds.

---

## Screenshots

| Before loading | During play |
|---|---|
| Dark themed launch screen | Red circles mark found differences; blue circles show revealed ones |

---

## Quick Start

### Step 1 — Check your Python version

> ⚠️ **Python 3.14 is NOT supported.**  
> `opencv-python` and `Pillow` do not have binary builds for Python 3.14 yet.  
> Use **Python 3.11 or 3.12** instead.

Download Python 3.11: https://www.python.org/downloads/release/python-3119/  
Choose the **macOS 64-bit universal2 installer**.

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

Or if you have multiple Python versions on your Mac:

```bash
/Library/Frameworks/Python.framework/Versions/3.11/bin/pip3 install -r requirements.txt
```

### Step 3 — Run the game

```bash
python main.py
```

Or with a specific Python version:

```bash
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 main.py
```

---

## How to Play

1. Click **Load Image** and choose any JPG, PNG, or BMP photo from your computer.
2. Two images appear side by side — the left is the **original**, the right is the **modified** copy.
3. The game automatically hides **5 differences** in the modified image.
4. Click on the **Modified** image (right side) where you think a difference is.
5. A **red circle** marks a correct find on both images.
6. You are allowed a maximum of **3 mistakes** per round.
7. If you get stuck, press **Reveal All** — blue circles show all unfound differences.
8. Press **Restart** to generate a fresh set of 5 differences on the same image.
9. Your **Total Score** carries over between rounds.

---

## Project Structure

```
find_the_difference/
│
├── main.py               Entry point — launches the application
├── game_gui.py           Tkinter GUI — all windows, widgets, and event handlers
├── game_state.py         Round lifecycle — click logic, mistakes, scoring
├── image_processor.py    OpenCV pipeline — load, generate, and scale images
├── alterations.py        Alteration class hierarchy (OOP demonstration)
├── difference_region.py  Data model for one hidden difference
│
├── requirements.txt      Python package dependencies
└── README.md             This file
```

**Important:** all six `.py` files must be in the **same folder**.  
Run `main.py` from that folder — do not run individual files like `game_gui.py` directly.

---

## OOP Concepts Demonstrated

### 1. Abstraction — `alterations.py`

`BaseAlteration` is an **Abstract Base Class** (ABC).  
It declares `apply()` as an abstract method, meaning any class that inherits from it *must* provide its own version of `apply()`.  
This prevents the base class from ever being used directly and enforces a consistent interface across all alteration types.

```python
class BaseAlteration(ABC):
    @abstractmethod
    def apply(self, image, region):
        ...  # subclasses must implement this
```

---

### 2. Inheritance — `alterations.py`

All four concrete alteration types extend `BaseAlteration`:

```
BaseAlteration  (abstract)
├── ColourShift
├── BlurAlteration
├── BrightnessAlteration
└── PixelateAlteration
```

Each subclass inherits the `_slice()` helper from the base class (so it is not repeated four times) and overrides `apply()` with its own image manipulation logic.

---

### 3. Polymorphism — `image_processor.py`

`ImageProcessor` holds a list of `BaseAlteration` objects.  
When generating differences it calls `alteration.apply(image, region)` without caring which subclass it is — Python automatically dispatches to the correct `apply()` method at runtime.

```python
alteration = random.choice(self._alterations)  # could be any subclass
alteration.apply(modified, region)             # correct method runs automatically
```

This is polymorphism: one call, multiple possible behaviours.

---

### 4. Encapsulation — `game_state.py`, `game_gui.py`

Private attributes (prefixed with `_`) store internal state and are never accessed directly from outside the class.  
Read-only `@property` descriptors expose only what other classes need to see.

```python
class GameState:
    def __init__(self):
        self._mistakes = 0        # private — cannot be changed from outside

    @property
    def mistakes(self) -> int:    # read-only public access
        return self._mistakes
```

The GUI reads `state.mistakes` but can never write `state._mistakes = 0` by accident.

---

### 5. Composition — `game_gui.py`

`GameGUI` does **not** inherit from `GameState` or `ImageProcessor`.  
Instead it **owns** them as member objects — this is composition.

```python
class GameGUI:
    def __init__(self, root):
        self._processor = ImageProcessor()   # composed in
        self._state     = GameState()        # composed in
```

`GameState` in turn owns a `list[DifferenceRegion]` — another layer of composition.

---

## Alteration Details

| Class | Visual effect | How it works |
|---|---|---|
| `ColourShift` | Subtle hue change | Converts patch to HSV, shifts H channel by 12–28° |
| `BlurAlteration` | Soft focus | Blends original with Gaussian blur (40 % original / 60 % blurred) |
| `BrightnessAlteration` | Lighter or darker patch | Adds ±18 or ±26 to every pixel value, clamped to 0–255 |
| `PixelateAlteration` | Mosaic / blocky patch | Downscales ÷ 8 then upscales back with nearest-neighbour interpolation |

All changes are intentionally subtle — clearly different on careful inspection, but not immediately obvious at a glance.

---

## Algorithm: Generating 5 Non-Overlapping Differences

```
REPEAT until 5 regions are placed (max 2 000 attempts):
    1. Pick a random (x, y, width, height) inside the image
    2. Check if the candidate overlaps any already-placed region
    3. If no overlap → accept it, pick a random alteration, apply it
    4. If overlap    → discard and try again
```

Overlap detection uses **Axis-Aligned Bounding Box (AABB) separation** plus a 20-pixel gap buffer, implemented in `DifferenceRegion.overlaps()`.

---

## UI Design

The interface uses a **dark navy theme** with **teal (`#2ec4b6`)** as the primary accent colour — chosen because it is vivid on dark backgrounds and rarely seen in university Python projects.

| Element | Colour | Purpose |
|---|---|---|
| Background | `#1e1e2e` | Easy on the eyes for long sessions |
| Header / Footer | `#252538` | Subtle contrast from the main bg |
| Teal accent | `#2ec4b6` | Modified canvas border, button hover, labels |
| Red marker | `#ff4f6a` | Found differences |
| Blue marker | `#4fb3ff` | Revealed (unfound) differences |
| Green counter | `#4fffa0` | Remaining differences label |
| Yellow timer | `#ffd166` | Elapsed time display |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `opencv-python` | ≥ 4.8 | Image loading, colour conversion, blur, resize |
| `Pillow` | ≥ 10.0 | Converting NumPy arrays to Tkinter PhotoImages |
| `numpy` | ≥ 1.24 | Pixel arithmetic (add, clip, type conversion) |

Install all at once:

```bash
pip install -r requirements.txt
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ImportError: cannot import name 'MAX_DISPLAY_HEIGHT'` | Old `image_processor.py` in your folder | Replace with the latest version from this project |
| `ModuleNotFoundError: No module named 'cv2'` | OpenCV not installed | `pip install opencv-python` |
| `ModuleNotFoundError: No module named 'tkinter'` | Wrong Python version (common on Python 3.14) | Use Python 3.11 or 3.12 |
| Blank / invisible buttons | macOS overriding button colours | Already fixed in the latest `game_gui.py` |
| Blue strip at bottom of canvas | Old `game_gui.py` with grid layout | Replace with the latest `game_gui.py` |
| App crashes on image load | Image format not supported | Use JPG, PNG, or BMP |

---

## Running the Tests

```bash
python test_core_logic.py
```

Expected output:
```
  PASS  test_processor_creates_five_non_overlapping_differences
  PASS  test_game_state_finds_region_and_locks_after_three_mistakes
  PASS  test_game_starts_unlocked_after_start_round
  PASS  test_locked_state_ignores_clicks
  PASS  test_region_overlaps_detects_collision
  PASS  test_reveal_unfound_marks_remaining_and_locks
  PASS  test_multiple_rounds_preserve_total_found

7 passed, 0 failed out of 7 tests.
```
