from tkinter import Tk
from typing import Literal


class TkWindow(Tk):
    """
    Util class for the windows.

    `window_mode` [optional]:
        - "dead"
            Instruct the window manager to ignore this widget and set `-topmost` to ``True``.
        - "headless"
            Set `-type` to ``"splash"`` and `-topmost` to ``True``.
        - "top"
            Set `-topmost` to ``True``.

    `drag` [optional]:
        Create the functionality to be able to move the window by holding it at any position.
    """

    fullscreen_height: int
    fullscreen_width: int

    def __init__(
            self,
            window_mode: Literal["dead", "headless", "top"] = None,
            drag: bool = True,
            resizable: tuple[bool, bool] = (False, False),
            title: str = "",
    ):
        Tk.__init__(self)

        self.resizable(*resizable)

        self.fullscreen_height = int(self.winfo_screenheight() * 0.0756)
        self.fullscreen_width = int(self.winfo_screenwidth() * 0.062)

        if window_mode:
            if window_mode == "dead":
                self.overrideredirect(True)
                self.attributes('-topmost', True)
            elif window_mode == "headless":
                self.wm_attributes('-type', 'splash')
                self.attributes('-topmost', True)
            elif window_mode == "top":
                self.attributes('-topmost', True)

        if drag:
            wx, wy = 0, 0

            def _drag(event):
                nonlocal wx, wy
                wx, wy = event.x, event.y

            def _move(event):
                self.geometry('+{0}+{1}'.format(event.x_root - wx, event.y_root - wy))

            self.bind('<Button-1>', _drag)
            self.bind('<B1-Motion>', _move)

        self.title(title)

    def resize(self, height: int, width: int):
        self.configure(height=height, width=width)
        self.focus_force()
