# -*- coding: utf-8 -*-
"""
Normalized-coordinate pointer control for Windows.

Why normalized coordinates?
    A screen position can be described three different ways, and they all
    disagree on a high-DPI display:

        physical pixels   2560 x 1600   (what the GPU actually draws)
        logical pixels    1707 x 1067   (what apps see, after 150% scaling)
        screenshot px     1500 x  938   (whatever your screenshot tool saved)

    If you hardcode any one of them, your pointer lands in the wrong place the
    moment the user changes scaling, resolution, or screenshot tool. Normalized
    coordinates sidestep all of it: 0-1000 across, 0-1000 down. You measure
    something on *any* screenshot by proportion, and it still works.

Pitfall #1 -- DPI awareness must be declared FIRST.
    A process that has not declared DPI awareness gets *scaled* screen metrics.
    On a 150% display, GetSystemMetrics returns 1707 instead of 2560, and
    SetCursorPos then interprets your numbers in that same scaled space. The
    cursor ends up at roughly two thirds of where you wanted. Call
    enable_dpi_awareness() before anything else touches the user32 API.

Pitfall #2 -- screenshot tools love to resize.
    The screenshot you measure against is almost never the same size as the
    screen. Always convert through a ratio, never assume 1:1.
"""
import ctypes
import time

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

_u = ctypes.windll.user32
_aware = False


def enable_dpi_awareness():
    """Declare per-monitor DPI awareness. Safe to call repeatedly."""
    global _aware
    if _aware:
        return
    try:
        # PROCESS_PER_MONITOR_DPI_AWARE
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            _u.SetProcessDPIAware()
        except Exception:
            pass
    _aware = True


def screen_size():
    """Physical size of the primary display, in real pixels."""
    enable_dpi_awareness()
    return _u.GetSystemMetrics(0), _u.GetSystemMetrics(1)


def to_pixels(nx, ny):
    """(0-1000, 0-1000) -> (physical x, physical y)."""
    w, h = screen_size()
    return int(round(nx / 1000.0 * w)), int(round(ny / 1000.0 * h))


def to_normalized(x, y):
    """(physical x, physical y) -> (0-1000, 0-1000)."""
    w, h = screen_size()
    return x / w * 1000.0, y / h * 1000.0


def cursor_pos():
    """Where the pointer actually is right now, in physical pixels."""
    enable_dpi_awareness()

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    p = POINT()
    _u.GetCursorPos(ctypes.byref(p))
    return p.x, p.y


def move_to(nx, ny):
    """Move the pointer to a normalized position. Returns the pixel it landed on."""
    x, y = to_pixels(nx, ny)
    _u.SetCursorPos(x, y)
    return x, y


def click(times=1, interval=0.12):
    """Left-click at the current pointer position."""
    for _ in range(times):
        _u.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.03)
        _u.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(interval)


def move_and_click(nx, ny, times=1, settle=0.15):
    """Move, let the UI react, then click. The settle delay matters: many
    apps only enable a control once hover/hit-testing has run."""
    x, y = move_to(nx, ny)
    time.sleep(settle)
    click(times)
    return x, y


def type_text(text):
    """Type arbitrary Unicode text (works for Chinese too) via synthetic
    Unicode key events. Does NOT press Enter -- the caller decides that."""
    enable_dpi_awareness()
    KEYEVENTF_UNICODE = 0x0004
    KEYEVENTF_KEYUP = 0x0002
    for ch in text:
        _u.keybd_event(0, ord(ch), KEYEVENTF_UNICODE, 0)
        _u.keybd_event(0, ord(ch), KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0)
        time.sleep(0.02)


if __name__ == "__main__":
    enable_dpi_awareness()
    w, h = screen_size()
    print("screen (physical): %d x %d" % (w, h))
    print("cursor now:       %s" % (cursor_pos(),))
    print("center of screen: %s" % (to_pixels(500, 500),))
