from __future__ import annotations

import tkinter as tk
import tkinter.ttk as ttk


class ManWidget(ttk.Notebook):
    """
    Create a multy-tap manual widget from ``iterable[(<tap-title>, <content>), ...]``.

    Styles in use:
            - manual.TNotebook
            - manual.TFrame
            - manual.Vertical
            - manual.TLabel
    """

    def __init__(
            self,
            master, *pages: tuple[str, str], height: int = 500, width: int = 800, **tk_kwargs
    ):
        ttk.Notebook.__init__(self, master, height=height, width=width, style="manual.TNotebook", **tk_kwargs)

        for n, i in enumerate(pages):
            label, text = i

            main_frame = ttk.Frame(self, style="manual.TFrame")

            main_frame.rowconfigure(0, weight=1)
            main_frame.columnconfigure(1, weight=1)

            scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, style="manual.Vertical.TScrollbar")

            canvas = tk.Canvas(
                main_frame,
                highlightthickness=0,
                yscrollcommand=scrollbar.set,
            )

            scrollbar.config(command=canvas.yview)
            canvas.yview_moveto(0)

            page = ttk.Frame(canvas, style="manual.TFrame")
            canvas.create_window(0, 0, window=page, anchor=tk.NW)

            text_label = ttk.Label(page, text=text, style="manual.TLabel")
            text_label.pack(expand=True, fill=tk.BOTH)

            def page_sizing(e, canvas=canvas, page=page):
                canvas.config(scrollregion="0 0 {0} {1}".format(page.winfo_reqwidth(), page.winfo_reqheight()))
                if page.winfo_reqwidth() is not canvas.winfo_width():
                    canvas.config(width=page.winfo_reqwidth())

            page.bind("<Configure>", page_sizing)

            def canvas_sizing(e, canvas=canvas, page=page):
                if page.winfo_reqwidth() is not canvas.winfo_width():
                    canvas.configure(width=page.winfo_reqwidth())

            canvas.bind("<Configure>", canvas_sizing)

            canvas.grid(row=0, column=1, sticky=tk.NSEW)
            scrollbar.grid(row=0, column=2, sticky=tk.NS)

            self.add(main_frame, text=label, sticky=tk.NSEW)

            def mouse(event, canvas=canvas):
                if event.delta:
                    canvas.yview_scroll(-1 * (event.delta // 100), "units")
                else:
                    canvas.yview_scroll({4: -1, 5: 1}[event.num], "units")

            canvas.bind("<MouseWheel>", mouse)
            canvas.bind("<Button-4>", mouse)
            canvas.bind("<Button-5>", mouse)
            text_label.bind("<MouseWheel>", mouse)
            text_label.bind("<Button-4>", mouse)
            text_label.bind("<Button-5>", mouse)


if __name__ == "__main__":
    pages = [
        ("Foobar",
         """
The terms foobar (/ˈfuːbɑːr/), foo, bar, baz, 
and others are used as metasyntactic variables 
and placeholder names in computer programming 
or computer-related documentation.
"""),
        ("[*]",
         "\n".join("*" * i for i in range(100))),
        ("Title3",
         """Bubblesort
         
55 07 78 12 42   i 1
07 55 78 12 42
07 55 78 12 42
07 55 12 78 42   last comparison
07 55 12 42 78   i 2
07 55 12 42 78
07 12 55 42 78   last comparison
07 12 42 55 78   i 3
07 12 42 55 78   last comparison
07 12 42 55 78   i 4
07 12 42 55 78   done
"""),

    ]
    mw = ManWidget(None, *pages)
    mw.pack()
    mw.mainloop()
