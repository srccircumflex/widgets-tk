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

from tkinter import Entry, Tk, Button
from tkinter import END, INSERT, SEL_FIRST, SEL_LAST
from sys import platform
from typing import Iterable


__all__ = ["PassEntry"]


class PassEntry(Entry):

    def __init__(self,
                 master,
                 show: chr = "*",
                 delay: int = 800,
                 getpass_range: Iterable = None,
                 getpass_call: ... = None,
                 getpass_del: bool = False,
                 **tk_kwargs,
                 ):

        """
        Password entry with delayed hiding. Alternative to `Entry(master, show="*")'.
        Supports all common character sets(1aA!), multy keys(^`˝) and under Linux also the alternative graphics(↑Ωł).

        {Deletes the input from the widget and writes it casually into a variable. Markings and the position
        of the cursor is respected.}


        howto get the password:
            - by protected member self._password
            - by calling self.getpass (args `getpass_*' executed here)
            - by calling self.get (args `getpass_*' executed here)


        :param master: root tk
        :param show: displayed char
        :param delay: hiding delay
        :param getpass_range: check password length
        :param getpass_call: callable, gets `self._password' as argument
        :param getpass_del: delete `self._password' and flush entry if True
        :param tk_kwargs: Valid resource names: background, bd, bg, borderwidth, cursor, exportselection, fg, font, foreground, highlightbackground, highlightcolor, highlightthickness, insertbackground, insertborderwidth, insertofftime, insertontime, insertwidth, invalidcommand, invcmd, justify, relief, selectbackground, selectborderwidth, selectforeground, state, takefocus, textvariable, validate, validatecommand, vcmd, width, xscrollcommand
        """

        self._password: str = ""

        self.delay: int = delay
        self.show: chr = show

        self.getpass_range: Iterable = getpass_range
        self.getpass_call: ... = getpass_call
        self.getpass_del: bool = getpass_del

        Entry.__init__(self, master, tk_kwargs)
        self.bind("<Key>", self._run)
        self.bind("<Button>", self._run)

        self._external: bool = False

        self.get = self.getpass

        if platform == "linux":
            # (
            # MultyKeys,                    ^ ` ọ ˇ
            # NoModifier,                   a b c d
            # Shift+Key,                    A B C D
            # AltGr+Key(AT-Layout),         @ ł | ~
            # AltGr+Shift+Key(AT-Layout)    Ω Ł ÷ ⅜
            # )
            self._states = (0, 16, 17, 144, 145)
        elif platform == "win32":
            # (
            # AltGr+Key(AT-Layout),         @ \ | }
            # NoModifier,                   a b c d
            # Shift+Key,                    A B C D
            # )
            self._states = (0, 8, 9)

    def _char(self, event) -> str:
        def del_mkey():
            i = self.index(INSERT)
            self._delete(i - 1, i)

        if event.keysym in ('Delete', 'BackSpace'):
            return ""
        elif event.keysym == "Multi_key" and len(event.char) == 2:  # windows stuff
            if event.char[0] == event.char[1]:
                self.after(10, del_mkey)
                return event.char[0]
            return event.char
        elif event.char != '\\' and '\\' in f"{event.char=}":
            return ""
        elif event.num in (1, 2, 3):
            return ""
        elif event.state in self._states:
            return event.char
        return ""

    def _get(self):
        return self.tk.call(self._w, 'get')

    def _delete(self, first, last=None):
        self.tk.call(self._w, 'delete', first, last)

    def _insert(self, index, string: str) -> None:
        self.tk.call(self._w, 'insert', index, string)

    def _run(self, event):

        if self._external and self._char(event):
            self._external = False
            self.clear()

        def hide(index: int, lchar: int):
            i = self.index(INSERT)
            for j in range(lchar):
                self._delete(index + j, index + 1 + j)
                self._insert(index + j, self.show)
            self.icursor(i)

        if event.keysym == 'Delete':
            if self.select_present():
                start = self.index(SEL_FIRST)
                end = self.index(SEL_LAST)
            else:
                start = self.index(INSERT)
                end = start + 1

            self._password = self._password[:start] + self._password[end:]

        elif event.keysym == 'BackSpace':
            if self.select_present():
                start = self.index(SEL_FIRST)
                end = self.index(SEL_LAST)
            else:
                if not (start := self.index(INSERT)):
                    return
                end = start
                start -= 1

            self._password = self._password[:start] + self._password[end:]

        elif char := self._char(event):
            if self.select_present():
                start = self.index(SEL_FIRST)
                end = self.index(SEL_LAST)
            else:
                start = self.index(INSERT)
                end = start

            self._password = self._password[:start] + char + self._password[end:]

            self.after(self.delay, hide, start, len(char))

    def insert(self, index, string: str) -> None:
        self._external = True
        self.tk.call(self._w, 'insert', index, string)

    def delete(self, first, last=None) -> None:
        self._external = True
        self.tk.call(self._w, 'delete', first, last)

    def clear(self):
        del self._password
        self._password = ""
        self._delete(0, END)

    def getpass(self):
        password = self._password
        if self.getpass_range:
            assert len(self._password) in self.getpass_range, f'## Password not in {self.getpass_range}'
        if self.getpass_call:
            password = self.getpass_call.__call__(self._password)
        if self.getpass_del:
            del self._password
            self._password = ""
            self._delete(0, END)
        return password


if __name__ == "__main__":

    t = Tk()

    from hashlib import sha256

    passwd_entry = PassEntry(
        master=t,

    #    getpass_range=range(8, 20),
    #    getpass_call=lambda _s: sha256(_s.encode()).hexdigest(),
    #    getpass_del=True,

        relief="sunken",
        width=58,
        font=('Consolas', 12),
        bg="#ADA5A5"
    )
    passwd_entry.insert(0, "<passentry>   *do not delete the entry*")
    passwd_entry.pack(pady=12, padx=8)

    passwd_out = Entry(t, width=58, font=('Consolas', 12), bg="#D3D7CF")
    passwd_out.pack(pady=4)

    def show(event):
        if event:
            passwd_out.delete(0, END)
            passwd_out.insert(0, "> " + passwd_entry._password + " <")
            passwd_out.after(500, show, False)
        else:
            passwd_out.delete(0, END)
            passwd_out.insert(0, passwd_entry._password)

    passwd_out.insert(0, "press <Return> to see the passphrase")

    Button(
        t, text="getpass() -> stdout", width=54, font=('Consolas', 12), command=lambda : print(passwd_entry.getpass())
    ).pack(pady=4)

    insert_entry = Entry(t, width=58, font=('Consolas', 12))
    insert_entry.pack(pady=12)
    insert_entry.insert(0, "insert <something> (press Alt-j to insert) / (Alt-d to delete)")

    for w in (t, passwd_out, insert_entry, passwd_entry):
        w.bind("<Return>", show)
        w.bind("<Alt-d>", lambda _: passwd_entry.delete(0, END))
        w.bind("<Alt-j>", lambda _: passwd_entry.insert(0, insert_entry.get()))

    t.mainloop()
