# normalized-pointer

Point at things on screen without ever hardcoding a pixel.

```python
from normalized_pointer import move_and_click

move_and_click(55, 197)   # 5.5% across, 19.7% down -- wherever that lands
```

If you write GUI automation, screen tutorials, or overlay pointers, you have
probably run into this: the same screen position has **three different
coordinates** depending on who is asking.

| Space | On a 2560×1600 display at 150% scaling |
|---|---|
| Physical pixels | 2560 × 1600 |
| Logical pixels (what apps see) | 1707 × 1067 |
| What your screenshot tool saved | 1500 × 938 |

Hardcode one and you break the moment scaling changes. Normalized coordinates
(`0–1000` across, `0–1000` down) survive all of it — you measure a position as
a proportion of *any* screenshot, and it still lands correctly.

## Install

No dependencies. Pure `ctypes` against `user32`.

```bash
pip install pillow        # only needed for locate.py
```

## Usage

```python
import normalized_pointer as np

np.enable_dpi_awareness()          # call this first, always
print(np.screen_size())            # (2560, 1600)
np.move_to(500, 500)               # pointer to dead center
print(np.cursor_pos())             # verify it actually got there
np.move_and_click(55, 197)         # move, settle, left-click
np.type_text("hello")              # Unicode-safe, no Enter pressed
```

Verifying that something landed where you wanted, from a screenshot:

```python
from locate import find_marker

pos, meta = find_marker("screen.png", rgb=(56, 128, 239))
print(pos)   # (523.0, 353.9) -- normalized position of the marker
```

## Three pitfalls this library exists to document

All three were found the hard way, and all three produce the same symptom:
**the pointer lands somewhere plausible but wrong**, which looks like a bug in
the *other* program.

### 1. Declare DPI awareness before touching user32

A process that has not declared DPI awareness receives **scaled** metrics. On a
150% display, `GetSystemMetrics(0)` returns `1707`, not `2560`. `SetCursorPos`
then interprets your arguments in that same scaled space, and the cursor lands
at roughly two thirds of the intended distance.

Measured: asking for the screen center of a 1707×1067 logical desktop put the
pointer at `(1281, 800)` physical instead of `(1707, 1067)`.

Fix: `SetProcessDpiAwareness(2)` once, at startup.

### 2. Your screenshot is not the size you think

A 2560×1600 screen captured as a 1500×938 JPEG. A 1080×675 preview rendered
from that. Measuring a position "as pixels" in whichever image you happen to
have is how coordinates drift by tens of pixels.

Fix: measure the *ratio*, never the raw pixel count. `cx / width * 1000`.

### 3. The label bubble lies about the center

Overlay pointers come with a text label, usually drawn in the same color as the
badge. Segment by color, take the bounding box, and the bubble merges in and
drags the center sideways.

Measured: a 78 px badge plus a 130 px bubble reported a center **40 logical
pixels** to the right of the truth. That is enough to spend an afternoon
"fixing" a bug that does not exist.

Fix: the badge is round, so each column through it spans nearly the full
diameter; the bubble is flat. Keep only columns with a large vertical span.
`locate.py` does this.

### Bonus: animations are not done when you think they are

If the thing you are measuring flies to its destination with an easing curve,
screenshotting too early measures a position mid-flight.

Measured on the same target: 3 s after the call the marker read `817.3`; at 8 s
it read `824.0`. Same target, same code. If your verification screenshots do
not wait for the animation, your accuracy numbers are meaningless.

## License

MIT. Do whatever you want with it.
