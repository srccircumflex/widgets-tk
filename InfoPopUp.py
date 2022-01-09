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

from tkinter import Menu, Widget
from tkinter import RIGHT, DISABLED
from tkinter.font import nametofont
from typing import Iterable


__all__ = ["InfoPopUp"]


class InfoPopUp(Menu):
    def __init__(self,
                 target: Widget,
                 info_lines: Iterable,
                 relpos: tuple[int, int] = (10, 10),
                 timers: tuple[int, int, int] = (2000, 500, 0),
                 foreground: str = '#000000',
                 background: str = '#FFFFFF',
                 font=('Consolas', 7),
                 pre_pop_call: ... = None
                 ):

        """
        Tk-popup-menu to function as info-/disclaimer-popup.

        info_lines = [
          - str,  --> line;
          - str,  --> line;
          - None, --> ------------------;
          - str   --> line
        ]

        :param target: the target widget
        :param info_lines: [str=line, None=separator]
        :param relpos: x/y adjustment
        :param timers: ms (do popup, popup leaving closing, target leaving closing)
        :param foreground: info-popup foreground (-> Menu.disabledforeground & Menu.activeforeground)
        :param background: info-popup background (-> Menu.background & Menu.activebackground)
        :param font: tk font
        :param pre_pop_call: called before popup
        """

        self.pop_pos = relpos[0], relpos[1]
        self.popup_timer, self.unpost_timer, self.clear_timer = timers

        self.pre_pop_call = (pre_pop_call if pre_pop_call else lambda: None)

        Menu.__init__(self,
                      target,
                      tearoff=0,
                      disabledforeground=foreground, activeforeground=foreground,
                      bg=background, activebackground=background,
                      bd=0, activeborderwidth=0
                      )

        for _line in info_lines:
            if _line is None:
                self.add_separator()
            else:
                self.add_command(
                    label=_line,
                    compound=RIGHT,
                    font=font,
                    state=DISABLED
                )

        target.bind("<Enter>", self._popup)
        target.bind("<Leave>", self._clear)
        target.bind("<Button>", lambda _: self.unpost())
        self.bind("<Enter>", lambda _: self.focus.__setitem__(1, True))
        self.bind("<Leave>", self._upost)
        self.focus = [False, False]
        self.posted = False

    def _suppress(self, _):
        self.focus = [False, False]
        self.posted = False

    def _clear(self, _):
        self.focus[0] = False

        def clear():
            if True not in self.focus:
                self.unpost()
                self.posted = False

        self.after(self.clear_timer, clear)

    def _popup(self, _):
        self.focus[0] = True
        if self.posted: return

        def popup():
            if not self.focus[0]: return
            self.pre_pop_call()
            wf = self.focus_get()
            try:
                self.tk_popup(
                    self.winfo_pointerx() + self.pop_pos[0],
                    self.winfo_pointery() + self.pop_pos[1])
            finally:
                if wf: wf.focus_force()
                self.grab_release()
                self.posted = True

        self.after(self.popup_timer, popup)

    def _upost(self, _):
        self.focus[1] = False
        if True in self.focus: return

        def upost():
            try:
                self.unpost()
            finally:
                self.posted = False

        self.after(self.unpost_timer, upost)


if __name__ == "__main__":
    from tkinter import Tk, Label, Button

    t = Tk()
    t.geometry("256x256")

    label = Label(t, text="Label")
    label.pack(pady=3)

    button = Button(t, text="Button")
    button.pack(pady=3)

    o_o = Label(t, text="o.o")
    o_o.pack(anchor="ne", pady=3)

    bigger_area = Label(t, text="bigger area", height=100, width=100, background='black', foreground='white')
    bigger_area.pack()

    InfoPopUp(label, ['info line of label'], timers=(0, 0, 0), font=("Consolas", 10))

    InfoPopUp(button, ['info line', 'with new line', None, 'and separator'])

    InfoPopUp(o_o,
              ['...'],
              relpos=(-2, -2),
              timers=(5000, 100, 100),
              foreground='white',
              background='pink',
              font=nametofont("TkFixedFont"))

    bigger_area_pop = InfoPopUp(bigger_area, ['actual position ...'])


    def pre_configure():
        bigger_area_pop.entryconfigure(0,
                                       label='actual position: x=%d y=%d' % (
                                           bigger_area_pop.winfo_pointerx(),
                                           bigger_area_pop.winfo_pointery()
                                       ))


    bigger_area_pop.pre_pop_call = pre_configure

    t.mainloop()
