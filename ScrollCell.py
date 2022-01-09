# MIT License
#
# Copyright (c) 2022 Adrian F. Hoefflin [srccircumflex]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from tkinter import LabelFrame, Canvas, Scrollbar, Frame, Pack, Grid, Place, Widget
from typing import Literal


__all__ = ["ScrollCell"]


v_EVENTS = ("<Button-4>", "<Button-5>", "<MouseWheel>")
V_EVENTS = ("<Next>", "<Prior>")
h_EVENTS = ("<Control-Button-4>", "<Control-Button-5>", "<Control-MouseWheel>")
H_EVENTS = ("<Control-Right>", "<Control-Left>")

FACTORIZING_KEYSYM = ("Down", "Up", "Next", "Prior", "Right", "Left")
INVERT_KEYSYM = ("Down", "Right", "Next")


class ScrollCell(Frame):

    def __init__(self,
                 master,
                 reverse_scroll: bool = True,
                 VH_factors: tuple = (6, 8),
                 cell_kwargs: dict = None,
                 scrollbar_y_kwargs: dict = None,
                 scrollbar_x_kwargs: dict = None,
                 orient_gr_width: Literal["sum", "widget", ""] = False,
                 orient_gr_height: Literal["sum", "widget", ""] = False,
                 auto_bind_mod: Literal["v", "h", "V", "H", "vh", "vH", "Vh", "VH", ""] = None,
                 **_front_kwargs):

        """
        A vertical and horizontal scrollable window.
          - Autonomous binding of scroll events
          - Optional scrollbars
          - Factorization for specific events (VH_factors)
          - Manual binding of events to widgets at a higher level (self.scroll_update)

        Global variables (can be overwritten after initialization)
          - v_EVENTS = ("<Button-4>", "<Button-5>", "<MouseWheel>")
          - V_EVENTS = ("<Next>", "<Prior>")
          - h_EVENTS = ("<Control-Button-4>", "<Control-Button-5>", "<Control-MouseWheel>")
          - H_EVENTS = ("<Control-Right>", "<Control-Left>")

          - FACTORIZING_KEYSYM = ("Down", "Up", "Next", "Prior", "Right", "Left")
          - INVERT_KEYSYM = ("Down", "Right", "Next")


        :param master: the master widget
        :param reverse_scroll: defines the trend
        :param VH_factors: x/y scroll factors for the events in [VH]_EVENTS
        :param cell_kwargs: the kwargs of the cell (the static part)
        :param scrollbar_y_kwargs: scrollbar kwargs (default; must be False to disable this too)
        :param scrollbar_x_kwargs: scrollable kwargs (optional)
        :param orient_gr_width: the width of the cell is based on the widest widget ("widget") or the sum of all ("sum")
        :param orient_gr_height: the height of the cell is based on the highest widget ("widget") or the sum of all ("sum")
        :param auto_bind_mod: bind placed widgets automatically with the mode...
        :param _front_kwargs: the kwargs of the scrollable part
        """

        self.v_EVENTS = v_EVENTS
        self.V_EVENTS = V_EVENTS
        self.h_EVENTS = h_EVENTS
        self.H_EVENTS = H_EVENTS

        self.FACTORIZING_KEYSYM = FACTORIZING_KEYSYM
        self.INVERT_KEYSYM = INVERT_KEYSYM

        self.trend: int = (-1 if reverse_scroll else 1)
        self.VH_factors: tuple = VH_factors

        if cell_kwargs is None:
            cell_kwargs = dict()

        if scrollbar_y_kwargs is None and scrollbar_x_kwargs is None:
            scrollbar_y_kwargs = dict()

        self.orient_gr_width = orient_gr_width
        self.orient_gr_height = orient_gr_height
        self.auto_bind_mod = auto_bind_mod

        # *--_container-------------------------------------------------(geometry managers are directed hereon)----*
        # | +-------------------cell--------------------------------------------------------------------------+*--*|
        # | |o---------------------------------------front--------------(self)-------------------------------o||S ||
        # | ||                                                ^                                              |||C ||
        # | ||                                                                                               |||R ||
        # | ||                                                                                               |||O ||
        # | ||                                                                                               |||L ||
        # | || <                                                                                           > |||B ||
        # | ||                                                                                               |||A ||
        # | ||                                                                                               |||R ||
        # | ||                                                                                               |||  ||
        # | ||                                                                                               |||Y ||
        # | ||                                                                                               |||  ||
        # | ||                                                v                                              |||  ||
        # | |o-----------------------------------------------------------------------------------------------o||  ||
        # | +-------------------------------------------------------------------------------------------------+*--*|
        # |*------------------------------------------------------------------------------------------------------*|
        # ||  SCROLLBAR X                                                                                         ||
        # |*------------------------------------------------------------------------------------------------------*|
        # *--------------------------------------------------------------------------------------------------------*

        self._container = LabelFrame(master)

        _scrollcommands = {}

        if isinstance(scrollbar_x_kwargs, dict):
            self.scrollbar_x = Scrollbar(self._container,
                                         orient="horizontal",
                                         **scrollbar_x_kwargs)
            self.scrollbar_x.pack(side="bottom", fill="x")

            _scrollcommands |= {'xscrollcommand': self.scrollbar_x.set}

        if isinstance(scrollbar_y_kwargs, dict):
            self.scrollbar_y = Scrollbar(self._container,
                                         orient="vertical",
                                         **scrollbar_y_kwargs)
            self.scrollbar_y.pack(side="right", fill="y")

            _scrollcommands |= {'yscrollcommand': self.scrollbar_y.set}

        self.cell = Canvas(self._container, **cell_kwargs)
        self.cell.pack(side="right")

        Frame.__init__(self, self.cell, **_front_kwargs)

        self.cell.create_window((0, 0),
                                window=self,
                                anchor="nw")

        # scroll config

        self.cell.config(_scrollcommands)

        if isinstance(scrollbar_x_kwargs, dict):
            self.scrollbar_x.config(command=self.cell.xview)
        if isinstance(scrollbar_y_kwargs, dict):
            self.scrollbar_y.config(command=self.cell.yview)

        self.cell.bind('<Configure>', self._update_scroll)
        self.bind('<Configure>', self._update_scroll)
        self.bind('<Expose>', self.__expose)

        m = (auto_bind_mod if auto_bind_mod else "v")
        self.scroll_update(self.cell, m)
        self.scroll_update(self, m)

        # define the self geometry methods to those of the _container

        for geo_meth in Pack.__dict__.keys() | Grid.__dict__.keys() | Place.__dict__.keys():
            if not geo_meth.startswith('_') and geo_meth != 'config' and geo_meth != 'configure':
                setattr(self, geo_meth, getattr(self._container, geo_meth))

    def __orient_gr_width(self, *_):
        def width():
            return {
                "sum": self.winfo_width,
                "widget": max(self.winfo_children(), key=lambda w: w.winfo_width()).winfo_width
            }[self.orient_gr_width]()

        self.config_cell(
            width=width()
        )

    def __orient_gr_height(self, *_):
        def height():
            return {
                "sum": self.winfo_height,
                "widget": max(self.winfo_children(), key=lambda w: w.winfo_height()).winfo_height
            }[self.orient_gr_height]()

        self.config_cell(
            height=height()
        )

    def __expose(self, *_):
        if self.orient_gr_width:
            self.__orient_gr_width()
        if self.orient_gr_height:
            self.__orient_gr_height()
        if self.auto_bind_mod:
            for w in self.winfo_children():
                self.scroll_update(w, self.auto_bind_mod)

    def __scroll_val(self, e, factor: int = 1) -> int:
        u = self.trend
        if e.num == 5 or e.delta < 0 or e.keysym in self.INVERT_KEYSYM: u = ~ u + 1
        if e.keysym in self.FACTORIZING_KEYSYM: u *= factor
        return u

    def __scroll_x(self, e):
        self.scroll_x(self.__scroll_val(e, self.VH_factors[0]))

    def __scroll_y(self, e):
        self.scroll_y(self.__scroll_val(e, self.VH_factors[1]))

    def _scroll_x(self, e):
        # This method is bound to the events
        # Additional code here (for inheritance)
        self.__scroll_x(e)

    def _scroll_y(self, e):
        # This method is bound to the events
        # Additional code here (for inheritance)
        self.__scroll_y(e)

    def scroll_x(self, z: int) -> None:
        self.cell.xview_scroll(z, "units")

    def scroll_y(self, z: int) -> None:
        self.cell.yview_scroll(z, "units")

    def scroll_update(self, __add_w: Widget, bind_mod: Literal["v", "h", "V", "H", "vh", "vH", "Vh", "VH"] = "v") -> None:
        """
        Bind the events in *_EVENTS to a widget.
          - [vV] = vertical scroll
          - [hH] = horizontal scroll
        Uppercase additionally binds the events in the corresponding *_EVENTS to the lowercase *_EVENTS.

        :param __add_w: the target widget
        :param bind_mod: the bind mode
        """
        vert = {event: self._scroll_y for event in self.v_EVENTS}
        VERT = vert | {event: self._scroll_y for event in self.V_EVENTS}
        hori = {event: self._scroll_x for event in self.h_EVENTS}
        HORI = hori | {event: self._scroll_x for event in self.H_EVENTS}
        _mod = {
            "v": vert,
            "h": hori,
            "V": VERT,
            "H": HORI,
            "vh": vert | hori,
            "vH": vert | HORI,
            "Vh": VERT | hori,
            "VH": VERT | HORI
        }
        for binding in _mod[bind_mod].items():
            __add_w.bind(*binding)

    def _update_scroll(self, *_):
        self.cell.update_idletasks()
        self.cell.config(scrollregion=self.cell.bbox("all"))

    def config_container(self, **kwargs) -> None:
        self._container.config(kwargs)

    def config_cell(self, **kwargs) -> None:
        self.cell.config(kwargs)

    def config_scrollbar(self, **kwargs) -> None:
        self.scrollbar_y.config(kwargs)


if __name__ == "__main__":
    from tkinter import Button, Label, Entry, Text, Tk

    t = Tk()
    t.geometry("600x400")
    t.maxsize(1600, 1600)

    _cell_kwargs = dict(width=800, height=800)

    # disable both scrollbars (still process scroll events)
    example1 = dict(scrollbar_y_kwargs=False)

    # activate both scrollbars
    example2 = dict(scrollbar_y_kwargs=dict(), scrollbar_x_kwargs=dict())

    # use the width of the widest widget as a guide
    example3 = dict(orient_gr_width="widget")

    # orient to the sum of all heights
    example4 = dict(orient_gr_height="sum")

    sc_front = ScrollCell(
        t,
        auto_bind_mod="VH",
        cell_kwargs=_cell_kwargs,
        **example2# | example4
    )

    # put some widgets on the front
    for i in (0, 10):

        for col in range(10):
            Button(sc_front, text="Button %d" % col).grid(row=0 + i, column=col)

        _container = Label(sc_front, bg="black")
        _container.grid(row=1 + i, column=0, columnspan=10)

        for col in range(6):
            # these are outside the automatic binding method
            button = Button(_container, text="Button 1 - %d" % col)
            button.grid(row=0 + i, column=col, padx=20)
            if i == 0:
                sc_front.scroll_update(button, "VH")

        for row in range(8):
            Entry(sc_front).grid(row=2 + i + row, column=0)

        Text(sc_front).grid(row=2 + i, column=1, rowspan=8)

        Text(sc_front, width=180).grid(row=2 + i, column=2, rowspan=8)

        for row in range(7):
            Entry(sc_front).grid(row=2 + i + row, column=3)

    sc_front.pack(fill="both")

    # configuration of the different layers
    sc_front.config(bg="red")
    sc_front.config_cell(bg="blue")
    sc_front.config_container(bg="magenta")

    t.mainloop()
