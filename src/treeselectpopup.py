from __future__ import annotations

import tkinter.ttk as ttk
from tkinter import font as tkFont
from typing import Literal, Iterable, Callable

from ._man_treeselectpopup import MANUAL
from .tkserver import TkBgServer, TkBgReceiver, TkBgWrapper
from .tkwindow import TkWindow
from .treeselect import TreeNode, SelectTreeWidget, TagsConfig


def __default_ttk_styler(style: ttk.Style):
    style.configure(
        "select.Treeview",
        weight="normal",
        size=10
    )
    __nav_font = tkFont.Font(style.master)
    __nav_font.configure(underline=True, weight="bold", size=10)
    style.map('select.Treeview', font=[('selected', __nav_font)], background=[], foreground=[('selected', '#000000')])

    __exp_font = tkFont.Font(style.master)
    __exp_font.configure(weight="normal", size=10)
    style.map(
        "expand.TButton",
        foreground=[('active', 'blue')],
        background=[('active', '#FFFFFF')],
        relief=[('active', 'flat')],
    )
    style.configure(
        "expand.TButton",
        background="#FFFFFF",
        foreground="#000000",
        relief="flat",
        font=__exp_font
    )

    style.configure(
        "confirm.TFrame",
        background="#FFFFFF",
    )

    __ccl_font = tkFont.Font(style.master)
    __ccl_font.configure(weight="normal", size=9)
    __ccl_a_font = tkFont.Font(style.master)
    __ccl_a_font.configure(weight="bold", size=9, underline=False, overstrike=True)
    style.map(
        "cancel.TButton",
        foreground=[('active', 'red')],
        background=[('active', '#FFFFFF')],
        relief=[('active', 'flat')],
        font=[('active', __ccl_a_font)],
    )
    style.configure(
        "cancel.TButton",
        background="#FFFFFF",
        foreground="#000000",
        relief="flat",
        font=__ccl_font
    )
    __man_font = tkFont.Font(style.master)
    __man_font.configure(family="monospace")
    style.configure(
        "manual.TLabel",
        font=__man_font
    )

    __cnf_font = tkFont.Font(style.master)
    __cnf_font.configure(weight="normal", size=9)
    __cnf_a_font = tkFont.Font(style.master)
    __cnf_a_font.configure(weight="bold", size=9, underline=True, overstrike=False)
    style.map(
        "confirm.TButton",
        foreground=[('active', 'blue')],
        background=[('active', '#FFFFFF')],
        relief=[('active', 'flat')],
        font=[('active', __cnf_a_font)],
    )
    style.configure(
        "confirm.TButton",
        background="#FFFFFF",
        foreground="#000000",
        relief="flat",
        font=__cnf_font
    )

    __hlp_font = tkFont.Font(style.master)
    __hlp_font.configure(weight="normal", size=7)
    style.configure(
        "help.TLabel",
        background="#FFFFFF",
        foreground="#555555",
        relief="flat",
        font=__hlp_font
    )

    return locals()


def treepopup(
        *structure: TreeNode,
        checked_iids: Iterable[TreeNode | str] = (),
        check_mode: Literal[
            "multi",
            "single",
            "single entry",
            "single sector",
        ] = "multi",
        at_focus_out: Literal["cancel", "confirm"] = None,
        window_mode: Literal["dead", "headless", "fullscreen", "top"] = False,
        window_drag: bool = True,
        window_title: str = "Tree Select Popup",
        window_height: int = 70,
        window_width: int = 50,
        server_address: tuple[str, int] | Iterable[tuple[str, int]] = ("127.0.0.11", 50_000),
        server_daemon: bool = True,
        return_mode: Literal[
            "receiver",
            "wait value",
            "instand value",
            "value at action"
        ] = "wait value",
        tags_config_update: TagsConfig = TagsConfig(),
        ttk_styler: Callable[[ttk.Style], dict] | None = __default_ttk_styler
) -> TkBgReceiver[list[TreeNode | None]] | list[TreeNode | None]:
    """
    Factory function for the :class:`SelectTreeWidget` as a popup window with the assistance of :class:`TkBgWrapper` and :class:`TkWindow`.

    Own parameters:
        - `at_focus_out` Literal["cancel", "confirm"]
            If defined, the corresponding action is executed, the server is closed and tk is destroyed if the focus is no longer on the window.
        - `return_mode` Literal["receiver", "wait value", "instand value", "value at action"] = "wait value"
            - "receiver"
                Return the :class:`TkBgReceiver`
            - "wait value"
                Wait until the current selection is confirmed or canceled and return the selected entries.
            - "instand value"
                Return selected entries directly after the start.
            - "value at action"
                Return the selected entries at the first interaction.

    ````

    Additional Keybindings:

        - widget.cancel_button
            - "<Button-1>": cancel
            - "<Return>": cancel
            - "<space>": cancel
        - widget.confirm_button
            - "<Button-1>": confirm
            - "<Return>": confirm
            - "<space>": confirm
        - root
            - "<Escape>": cancel
            - "<Control-c>": cancel
            - "<Control-Return>": confirm
            - "<F2>": resize window to (40, 100)
            - "<F3>": resize window to (40, 200)
            - "<F4>": resize window to (60, 100)
            - "<F5>": resize window to (60, 200)
            - "<F6>": resize window to (75, 100)
            - "<F7>": resize window to (75, 200)
            - "<F8>": resize window to (70, 50)
    """

    @TkBgWrapper(
        address=server_address,
        process_daemon=server_daemon,
        instand_return=return_mode in ("wait value", "instand value", "value at action"),
    )
    def func(server: TkBgServer, window_width=window_width, window_height=window_height):

        if window_mode == "fullscreen":
            root = TkWindow(
                window_mode="headless",
                drag=False,
                title=window_title
            )
            window_width, window_height = root.fullscreen_width, root.fullscreen_height
        else:
            root = TkWindow(
                window_mode=window_mode,
                drag=window_drag,
                title=window_title
            )

        widget = SelectTreeWidget(
            root,
            *structure,
            mode=check_mode,
            checked_iids=checked_iids,
            tags_config_update=tags_config_update,
            ttk_styler=ttk_styler,
            man_pages=MANUAL,
            man_title="[help] " + window_title
        )
        widget.pack()

        def sizing(e):
            if return_mode == "instand value":
                return confirm(None)

            if not widget.resize(window_height, window_width):
                return

            root.resize(window_height, window_width)

            children = widget.tree.get_children()
            if children:
                widget.tree.selection_set(children[0])
                widget.tree.focus_set()
                widget.tree.focus(children[0])

            root.unbind("<Configure>", sizing_b)

        sizing_b = root.bind("<Configure>", sizing)

        def fin(obj):
            server.send(obj)
            server.exit()

        def cancel(e):
            fin(None)

        widget.cancel_button.bind("<Button-1>", cancel)
        widget.cancel_button.bind("<Return>", cancel)
        widget.cancel_button.bind("<space>", cancel)
        root.bind("<Escape>", cancel)
        root.bind("<Control-c>", cancel)

        def confirm(e):
            fin(widget.tree.get_checked())

        widget.confirm_button.bind("<Button-1>", confirm)
        widget.confirm_button.bind("<Return>", confirm)
        widget.confirm_button.bind("<space>", confirm)
        root.bind("<Control-Return>", confirm)

        if at_focus_out:
            if at_focus_out == "confirm":
                root.bind("<FocusOut>", lambda e: (confirm(None) if e.widget == root else None))
            else:
                root.bind("<FocusOut>", lambda e: (cancel(None) if e.widget == root else None))

        if return_mode == "value at action":
            widget.tree.bind("<Return>", confirm, add=True)
            widget.tree.bind("<space>", confirm, add=True)
            widget.tree.bind("<Button-1>", confirm, add=True)
            widget.tree.bind("<Double-Button-1>", confirm, add=True)
            widget.tree.bind("#", confirm, add=True)

        root.bind("<F2>", lambda _: widget.resize(40, 100))
        root.bind("<F3>", lambda _: widget.resize(40, 200))
        root.bind("<F4>", lambda _: widget.resize(60, 100))
        root.bind("<F5>", lambda _: widget.resize(60, 200))
        root.bind("<F6>", lambda _: widget.resize(75, 100))
        root.bind("<F7>", lambda _: widget.resize(75, 200))
        root.bind("<F8>", lambda _: widget.resize(70, 50))

        return root

    return func()
