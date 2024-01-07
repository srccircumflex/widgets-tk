from __future__ import annotations

import json
import tkinter as tk
import tkinter.ttk as ttk
from os import environ
from pathlib import Path
from re import Pattern, search, compile, IGNORECASE, error as ReError, escape
from tkinter.filedialog import askopenfile, asksaveasfile
from typing import Generator, Callable
from typing import Literal, Any, Iterable

from ..manwidget import ManWidget


class TagsConfig:
    """
    The object defines the styling of the basistags:
        search hits:
            - match_*
        check status:
            - uncheck_entry
            - check_entry
            - uncheck_sector
            - check_sector
            - ccstate_sector
        entry types:
            - type_*

    Additional tags can be defined via kwargs.

    Updateable like dict.
    """

    t_entry = "t-entry"
    t_sector = "t-sector"
    t_top_sector = "t-sector-top"
    t_sub_sector = "t-sector-sub"
    c_check_entry = "c-check"
    c_uncheck_entry = "c-uncheck"
    c_check_sector = "c-check-sector"
    c_uncheck_sector = "c-uncheck-sector"
    c_ccstate_sector = "c-ccstate-sector"
    m_match_entry = "m-1-entry"
    m_match_sector = "m-1-sector"
    m_hint_sector = "m-2-sector"
    m_match_and_hint_sector = "m-3-sector"

    def __init__(
            self,
            match_entry: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            match_sector: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            match_hint_sector: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            match_hint_and_match_sector: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            uncheck_entry: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            check_entry: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            uncheck_sector: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            check_sector: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            ccstate_sector: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            type_entry: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            type_sector: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            type_top_sector: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            type_sub_sector: dict[Literal["foreground", "background", "font", "image"] | str, Any] = None,
            **kwargs: dict[Literal["foreground", "background", "font", "image"] | str, Any]
    ):
        config = {
                     TagsConfig.c_check_entry: check_entry,
                     TagsConfig.c_uncheck_entry: uncheck_entry,
                     TagsConfig.c_check_sector: check_sector,
                     TagsConfig.c_uncheck_sector: uncheck_sector,
                     TagsConfig.c_ccstate_sector: ccstate_sector,
                     TagsConfig.m_match_entry: match_entry,
                     TagsConfig.m_match_sector: match_sector,
                     TagsConfig.m_hint_sector: match_hint_sector,
                     TagsConfig.m_match_and_hint_sector: match_hint_and_match_sector,
                     TagsConfig.t_entry: type_entry,
                     TagsConfig.t_sector: type_sector,
                     TagsConfig.t_top_sector: type_top_sector,
                     TagsConfig.t_sub_sector: type_sub_sector,
                 } | kwargs
        self.config = {k: v for k, v in config.items() if v is not None}

    def configure(self, tree: ttk.Treeview):
        """configures a ttk.Treeview with this"""
        for tag, kw in self.config.items():
            # (Trial-and-Error knowledge)
            # If the PhotoImages are not saved in an attribute of the object, they are not displayed.
            # They are probably deleted in the process by the garbage collector.
            for itm in kw.items():
                attr = "_%s_%s" % (tag, itm[0])
                setattr(tree, attr, itm[1])
                kw[itm[0]] = getattr(tree, attr)

            tree.tag_configure(tag, **kw)

    def __or__(self, other: TagsConfig):
        """like: dict | dict"""
        new = TagsConfig()
        new.config = self.config | other.config
        return new


class TreeNode(dict):
    """
    This object defines a tree node and can be used to define the structure.

    `iid_path` is set after :class:`SelectTree` has created the structure or ``make_iid_paths`` has been executed.

    The SelectTree uses this type for return values.

    `checked`, `opened` and `tags` are updated in this case and a new object is returned.
    """

    @property
    def label(self) -> str:
        """ttk.Treeview named it 'text'"""
        return self["label"]

    @label.setter
    def label(self, val):
        """ttk.Treeview named it 'text'"""
        self["label"] = val

    @property
    def values(self) -> Any:
        return self["values"]

    @values.setter
    def values(self, val):
        self["values"] = val

    @property
    def children(self) -> tuple[TreeNode]:
        return self["children"]

    @children.setter
    def children(self, val):
        self["children"] = val

    @property
    def iid(self) -> str:
        return self["iid"]

    @iid.setter
    def iid(self, val):
        self["iid"] = val

    @property
    def iid_path(self) -> str:
        return self["iid_path"]

    @iid_path.setter
    def iid_path(self, val):
        self["iid_path"] = val

    @property
    def checked(self) -> bool | None:
        """None indicates checked children's"""
        return self["checked"]

    @checked.setter
    def checked(self, val):
        """None indicates checked children's"""
        self["checked"] = val

    @property
    def opened(self) -> bool:
        return self["opened"]

    @opened.setter
    def opened(self, val):
        self["opened"] = val

    @property
    def tags(self) -> tuple[str, ...]:
        return self["tags"]

    @tags.setter
    def tags(self, val):
        self["tags"] = val

    parent: TreeNode = None

    @property
    def iid_sep(self) -> str:
        return self["iid_sep"]

    @iid_sep.setter
    def iid_sep(self, val):
        self["iid_sep"] = val

    def __init__(
            self,
            label: str,
            values: Any,
            *children: TreeNode,
            iid: str = None,
            checked: bool | None = None,
            opened: bool = False,
            tags: tuple[str, ...] = (),
            iid_sep: str = ".",
            _iid_path: str = ""
    ):
        dict.__init__(self)
        self.label = label
        self.values = values
        self.children = children
        self.iid = iid or label
        self.checked = checked
        self.opened = opened
        self.tags = tags
        self.iid_path = _iid_path
        self.iid_sep = iid_sep

    def from_treeitem(
            self,
            iid_path: str,
            opened: bool,
            tags: str | list[str] | tuple[str, ...],
            checked: bool | None
    ) -> TreeNode:
        if self.iid_path == iid_path:
            tn = self
        else:
            tn = self.get_children(iid_path)
        return TreeNode(
            tn.label,
            tn.values,
            *tn.children,
            iid=tn.iid,
            checked=checked,
            opened=opened,
            tags=tags,
            _iid_path=tn.iid_path
        )

    @classmethod
    def ROOT(cls, children: Iterable[TreeNode]) -> TreeNode:
        """Create a root point with `children` (used by :class:`SelectTree`)"""
        return TreeNode("", "", *children, iid_sep="", _iid_path="")

    def compile(self) -> set[bool, bool] | set[bool] | set:
        """Compile the `iid_path`'s and check-states."""

        def make(node: TreeNode):
            checks = set()
            for _child in node:
                _child.iid_path = node.iid_path + node.iid_sep + _child.iid
                _child.parent = node
                if _child.checked is None:
                    _child.checked = node.checked
                checks.add(_child.checked or False)
                checks |= make(_child)
            if len(checks) == 2:
                node.checked = None
            elif len(checks) == 1:
                node.checked = checks.pop()
            elif node.checked is None:
                node.checked = False
            return checks

        return make(self)

    def __iter__(self) -> Iterable[TreeNode]:
        """iter(self.children)"""
        return iter(self.children)

    def children_iid_paths_linear_iter(self) -> Generator[str]:
        """Generate all `iid_path`'s of children's recursive and unstructured."""

        def gen():
            yield self.iid_path
            for c in self.children:
                c: TreeNode
                ci = c.children_iid_paths_linear_iter()
                for i in ci:
                    yield i

        return gen()

    def children_linear_iter(self) -> Generator[TreeNode]:
        """Generate all children's recursive and unstructured."""

        def gen():
            yield self
            for c in self.children:
                c: TreeNode
                ci = c.children_linear_iter()
                for i in ci:
                    yield i

        return gen()

    def child_from_dicts(self, child_dicts: Iterable[dict]):
        """Set `children` from attribute dicts (recursive)."""
        self.children = tuple(TreeNode.from_dict(cd) for cd in child_dicts)

    @classmethod
    def from_dict(cls, __dict: dict) -> TreeNode:
        """Create a new :class:`TreeNode` from attribute dict (recursive)."""
        return TreeNode(
            __dict["label"],
            __dict["values"],
            *(TreeNode.from_dict(cd) for cd in __dict["children"]),
            iid=__dict["iid"],
            checked=__dict["checked"],
            opened=__dict["opened"],
            tags=__dict["tags"],
            _iid_path=__dict["iid_path"]
        )

    def get_children(self, iid_path: str, depth: bool = True) -> TreeNode:
        """Find a children of this :class:`TreeNode` [recursive]."""
        if depth:
            for c in self.children:
                if c.iid_path == iid_path:
                    return c
                try:
                    return c.get_children(iid_path)
                except KeyError:
                    pass
        else:
            for c in self.children:
                if c.iid_path == iid_path:
                    return c
        raise KeyError(iid_path)

    def get_children_only_by_iid(self, iid: str, depth: bool = True) -> TreeNode:
        """
        Find a children of this :class:`TreeNode` [recursive].

        May be unexpected result.
        """
        if depth:
            for c in self.children:
                if c.iid == iid:
                    return c
                try:
                    return c.get_children_only_by_iid(iid)
                except KeyError:
                    pass
        else:
            for c in self.children:
                if c.iid == iid:
                    return c
        raise KeyError(iid)


class SelectTree(ttk.Treeview):
    """
    This :class:`ttk.Treeview` with parameters
    
    - *structure
        :class:`TreeNode`
    - tags_config
        :class:`TagsConfig` = TagsConfig()
    - master
        <tk> = None
    - width
        int = None
    - _restructure
        bool = True

        Must be left at True if the structure is not compiled.
    - **tk_kwargs
        piped to ttk.Treeview
    
    includes some additional util methods:
    
    - dump
    - load
    - get
    - search
    - get_matches
    - get_next_match
    - selection_to_next_match
    - expand_for_match
    - remove_match_tags
    - toggle_check
    - toggle_single_check
    - get_checked
    - is_checked
    - toggle_recursive_expand
    - element_by_event
    - event_points_to
    - iid_path_by_event
    - iid_path_by_selected
    - get_linear_iid_path_list
    - set_selection
    - set_width
    """

    top_sector_iids: tuple[str, ...]
    sub_sector_iids: tuple[str, ...]
    all_sector_iids: tuple[str, ...]
    entry_iids: tuple[str, ...]
    structure: TreeNode

    def __init__(
            self,
            *structure: TreeNode,
            tags_config: TagsConfig = TagsConfig(),
            master=None,
            width: int = None,
            _restructure: bool = True,
            **tk_kwargs
    ):
        ttk.Treeview.__init__(self, master, show="tree", **tk_kwargs)

        if width:
            self.set_width(width)

        tags_config.configure(self)

        self.load(structure, restructure=_restructure)

    def _change_check_tag(self, iid: str, tag: str):
        tags = set(self.item(iid, "tags"))
        for t in tags:
            if t.startswith("c-"):
                tags.remove(t)
                break
        tags.add(tag)
        self.item(iid, tags=tuple(tags))

    def _reset_match_tag(self, iid: str):
        tags = set(self.item(iid, "tags"))
        for t in tags:
            if t.startswith("m-"):
                tags.remove(t)
                break
        self.item(iid, tags=tuple(tags))

    def _add_match_tag(self, iid: str, tag: str):
        tags = set(self.item(iid, "tags"))
        for t in tags:
            if t.startswith("m-"):
                tag = "m-%s%s" % (
                    str(int(t[2]) | int(tag[2])),
                    t[3:]
                )
                tags.remove(t)
                break

        tags.add(tag)
        self.item(iid, tags=tuple(tags))

    def dump(self, start_iid: str = "") -> TreeNode:
        """Create a deepcopy from the current structure started from `start_iid`."""

        def dmp(iid=start_iid):
            tn = self.get(iid)
            tn.children = tuple(dmp(c.iid_path) for c in tn.children)
            return tn

        return dmp()

    def load(
            self,
            structure: Iterable[TreeNode],
            restructure: bool = False
    ) -> None:
        """
        Reset the entire structure.

        `restructure` must be left at True if the structure is not compiled (not required if structure comes from ``dump``).
        """
        self.delete(*self.get_children())

        top_sector_iids = list()
        sub_sector_iids = list()
        entry_iids = list()

        self.structure = TreeNode.ROOT(structure)

        if restructure:
            self.structure.compile()

            def make(struc, parent=""):
                for _node in struc:
                    _node: TreeNode
                    iid = _node.iid_path
                    tags = _node.tags
                    if _node.children:
                        if _node.parent.parent:
                            tags += (TagsConfig.t_sub_sector,)
                            sub_sector_iids.append(iid)
                        else:
                            tags += (TagsConfig.t_top_sector,)
                            top_sector_iids.append(iid)
                        if _node.checked is None:
                            tags += (TagsConfig.c_ccstate_sector,)
                        elif _node.checked:
                            tags += (TagsConfig.c_check_sector,)
                        else:
                            tags += (TagsConfig.c_uncheck_sector,)

                        self.insert(
                            parent,
                            text=_node.label,
                            values=_node.values,
                            index="end",
                            iid=iid,
                            tags=tags,
                            open=_node.opened
                        )

                        make(_node.children, iid)
                    else:
                        tags += (TagsConfig.t_entry,)
                        if _node.checked:
                            tags += (TagsConfig.c_check_entry,)
                        else:
                            tags += (TagsConfig.c_uncheck_entry,)

                        self.insert(
                            parent,
                            text=_node.label,
                            values=_node.values,
                            index="end",
                            iid=iid,
                            tags=tags,
                            open=_node.opened
                        )

                        entry_iids.append(iid)

        else:
            def make(struc, parent=""):
                for _node in struc:
                    _node: TreeNode
                    iid = _node.iid_path
                    tags = _node.tags
                    if _node.children:
                        self.insert(
                            parent,
                            text=_node.label,
                            values=_node.values,
                            index="end",
                            iid=iid,
                            tags=tags,
                            open=_node.opened
                        )
                        if not _node.parent.parent:
                            top_sector_iids.append(iid)
                        else:
                            sub_sector_iids.append(iid)

                        make(_node.children, iid)
                    else:
                        self.insert(
                            parent,
                            text=_node.label,
                            values=_node.values,
                            index="end",
                            iid=iid,
                            tags=tags,
                            open=_node.opened
                        )
                        entry_iids.append(iid)

        make(self.structure)

        self.top_sector_iids = tuple(top_sector_iids)
        self.sub_sector_iids = tuple(sub_sector_iids)
        self.all_sector_iids = self.top_sector_iids + self.sub_sector_iids
        self.entry_iids = tuple(entry_iids)

    def get(self, iid_path: str) -> TreeNode:
        """Return a copy with actual states of the entry on `iid_path`."""
        item = self.item(iid_path)
        tags = item["tags"]
        return self.structure.from_treeitem(
            iid_path,
            item["open"],
            tags,
            (None if TagsConfig.c_ccstate_sector in tags else (TagsConfig.c_check_entry in tags or TagsConfig.c_check_sector in tags))
        )

    def search(self, pattern: str | Pattern, parent_iid: str = "") -> bool:
        """Search for `pattern` started from `parent_iid`."""
        self.remove_match_tags()

        match = False

        def _search(_iid=parent_iid):
            nonlocal match
            children = self.get_children(_iid)
            for _iid in children:
                if search(pattern, self.item(_iid, "text")):

                    match = True

                    if _iid in self.all_sector_iids:
                        self._add_match_tag(_iid, TagsConfig.m_match_sector)
                    else:
                        self._add_match_tag(_iid, TagsConfig.m_match_entry)

                    def parentref(__iid=_iid):
                        parent = self.parent(__iid)
                        if parent:
                            self._add_match_tag(parent, TagsConfig.m_hint_sector)
                            parentref(parent)

                    parentref()

                _search(_iid)

        _search()

        return match

    def get_matches(self, parent_iid: str = "", scip_hints: bool = True, scip_sectors: bool = False) -> list[TreeNode]:
        """
        Return search results.

        - `parent_iid_path`
            Can be defined as a structure sector in which the next matches must be located.
        - `scip_hints`
            Skips search-hints of the sectors.
        - `scip_sectors`
            Skips all sectors.
        """
        matches = list()
        if scip_sectors:
            def find(_iid=parent_iid):
                children = self.get_children(_iid)
                for _iid in children:
                    itm = self.get(_iid)
                    if TagsConfig.m_match_entry in itm.tags:
                        matches.append(itm)
                    else:
                        find(_iid)
        elif scip_hints:
            def find(_iid=parent_iid):
                children = self.get_children(_iid)
                for _iid in children:
                    itm = self.get(_iid)
                    if (
                            TagsConfig.m_match_entry in itm.tags
                            or TagsConfig.m_match_sector in itm.tags
                            or TagsConfig.m_match_and_hint_sector in itm.tags
                    ):
                        matches.append(itm)
                    find(_iid)
        else:
            def find(_iid=parent_iid):
                children = self.get_children(_iid)
                for _iid in children:
                    itm = self.get(_iid)
                    for t in itm.tags:
                        if t.startswith("m-"):
                            matches.append(itm)
                    find(_iid)
        find()
        return matches

    def get_next_match(
            self,
            start_iid_path: str = None,
            parent_iid_path: str = "",
            scip_hints: bool = True,
            scip_sectors: bool = False,
            reverse: bool = False,
            back_to_begin: bool = False,
    ) -> TreeNode | None | Literal[False]:
        """
        Return the next search-match. Return False if there are no matches.

        - `start_iid_path`
            Starts searching at this point. If it is None, the currently selected entry is used.
        - `parent_iid_path`
            Can be defined as a structure sector in which the next match must be located.
        - `scip_hints`
            Skips search-hints of the sectors.
        - `scip_sectors`
            Skips sectors.
        - `reverse`
            Reverses the search order of top to bottom.
        - `back_to_begin`
            Returns the first/last match when the end of the order is reached. If left to False and matches are present, None is returned.
        """
        if matches := self.get_matches(
                parent_iid_path, scip_hints, scip_sectors
        ):
            start_iid_path: TreeNode | str
            if start_iid_path is None:
                start_iid_path = self.iid_path_by_selected()
            if reverse:
                matches.reverse()
            try:
                return matches[matches.index(start_iid_path) + 1]
            except IndexError:
                if back_to_begin:
                    return matches[0]
                else:
                    return
            except ValueError:
                matches_iids = [i.iid_path for i in matches]
                main_list = self.get_linear_iid_path_list()
                if reverse:
                    main_list.reverse()
                for i in main_list[main_list.index(start_iid_path):]:
                    try:
                        return matches[matches_iids.index(i)]
                    except ValueError:
                        pass
                if back_to_begin:
                    return matches[0]
                else:
                    return
        else:
            return False

    def selection_to_next_match(
            self,
            start_iid: str = None,
            parent_iid: str = "",
            scip_hints: bool = True,
            scip_sectors: bool = False,
            reverse: bool = False,
            back_to_begin: bool = False,
    ) -> TreeNode | None | Literal[False]:
        """
        Place the cursor on the next search match and return the match item. Return False if there are no matches.

        - `start_iid_path`
            Starts searching at this point. If it is None, the currently selected entry is used.
        - `parent_iid_path`
            Can be defined as a structure sector in which the next match must be located.
        - `scip_hints`
            Skips search-hints of the sectors.
        - `scip_sectors`
            Skips all sectors.
        - `reverse`
            Reverses the search order of top to bottom.
        - `back_to_begin`
            Returns the first/last match when the end of the order is reached. If left to False and matches are present, None is returned.
        """
        if match := self.get_next_match(start_iid, parent_iid, scip_hints, scip_sectors, reverse, back_to_begin):
            self.set_selection(match)
            self.focus(match)
        return match

    def expand_for_match(self) -> None:
        """Expand the tree to show search matches."""

        def x(_iid=""):
            for t in self.item(_iid, "tags"):
                if t.startswith("m-"):
                    self.item(_iid, open=True)
            children = self.get_children(_iid)
            for _iid in children:
                x(_iid)

        x()

    def remove_match_tags(self, parent_iid: str = ""):
        """Purge search-tags, started from `parent_iid` (recursive)."""

        def rm(_iid=parent_iid):
            children = self.get_children(_iid)
            for _iid in children:
                self._reset_match_tag(_iid)
                rm(_iid)

        rm()

    def toggle_check(self, check: bool = None, iid_path: str = "") -> bool:
        """Toggle or set the check state of entry on `iid_path` and return whether the entry is checked."""
        if iid_path:
            if iid_path in self.all_sector_iids:
                tag_check = TagsConfig.c_check_sector
                tag_uncheck = TagsConfig.c_uncheck_sector
            else:
                tag_check = TagsConfig.c_check_entry
                tag_uncheck = TagsConfig.c_uncheck_entry

            if check is None:
                check = tag_check not in self.item(iid_path, "tags")

            if check:
                tag = tag_check
            else:
                tag = tag_uncheck

            def __toggle_parents(_iid, _tag):
                self._change_check_tag(_iid, _tag)
                parent = self.parent(_iid)
                if parent:
                    children = self.get_children(parent)
                    states = set((TagsConfig.c_check_entry in (i := self.item(c, "tags")) or TagsConfig.c_check_sector in i) for c in children)
                    if all(states):
                        _tag = TagsConfig.c_check_sector
                    elif len(states) == 1:
                        _tag = TagsConfig.c_uncheck_sector
                    else:
                        _tag = TagsConfig.c_ccstate_sector
                    __toggle_parents(parent, _tag)

            __toggle_parents(iid_path, tag)

        elif check is None:
            check = not all((TagsConfig.c_check_sector in self.item(c, "tags")) for c in self.get_children(iid_path))

        if check:
            tag_entry = TagsConfig.c_check_entry
            tag_sector = TagsConfig.c_check_sector
        else:
            tag_entry = TagsConfig.c_uncheck_entry
            tag_sector = TagsConfig.c_uncheck_sector

        def __toggle_children(_iid):
            children = self.get_children(_iid)
            for _iid in children:
                if _iid in self.all_sector_iids:
                    self._change_check_tag(_iid, tag_sector)
                else:
                    self._change_check_tag(_iid, tag_entry)
                __toggle_children(_iid)

        __toggle_children(iid_path)

        return check

    def toggle_single_check(self, check: bool = None, iid_path: str = "") -> bool:
        """
        Purge all check states and toggle or set the check state of the entry on `iid_path`.

        Return whether the entry is checked.
        """
        if check is None:
            check = not self.is_checked(iid_path)
        self.toggle_check(False)
        self.toggle_check(check, iid_path)
        return check

    def get_checked(self) -> list[TreeNode]:
        """Return all checked entries."""
        checked = list()

        def get(iid):
            nonlocal checked
            item = self.item(iid)
            tags = item["tags"]
            if TagsConfig.c_check_entry in tags or TagsConfig.c_check_sector in tags:
                checked.append(self.structure.from_treeitem(iid, item["open"], tags, True))
            elif TagsConfig.c_ccstate_sector in tags:
                for child in self.get_children(iid):
                    get(child)

        for sector in self.get_children(""):
            get(sector)

        return checked

    def is_checked(self, iid_path: str) -> bool:
        """Return whether the entry on `iid_path` is checked."""
        tags = self.item(iid_path, "tags")
        return TagsConfig.c_check_entry in tags or TagsConfig.c_check_sector in tags

    def toggle_recursive_expand(self, start_iid: str = "", expand: bool = None) -> bool:
        """
        Toggle or set the extension of the structure from `start_iid`.

        Return whether the structure is extended.
        """
        if expand is None:
            if not start_iid:
                expand = True
                for sector in self.top_sector_iids:
                    if self.item(sector, "open"):
                        expand = False
                        break
            else:
                expand = not self.item(start_iid, "open")
        for sector in self.all_sector_iids:
            if sector.startswith(start_iid):
                self.item(sector, open=expand)
        return expand

    @staticmethod
    def element_by_event(event) -> str:
        """event.widget.identify("element", event.x, event.y)"""
        return event.widget.identify("element", event.x, event.y)

    def event_points_to(self, event, ref: Literal["image", "text", "indicator"] | str = None) -> Literal["image", "text", "indicator"] | None | bool:
        """
        Returns whether the event points to one of the elements ("image", "text", "indicator") if `ref` is not None.

        Otherwise, return the name of the element.
        """
        element = self.element_by_event(event)
        if "image" in element:
            e = "image"
        elif "text" in element:
            e = "text"
        elif "indicator" in element:
            e = "indicator"
        else:
            e = None
        if ref is not None:
            return (e or "") == ref
        else:
            return e

    def iid_path_by_event(self, event) -> str:
        """self.identify_row(event.y)"""
        return self.identify_row(event.y)

    def iid_path_by_selected(self) -> str:
        """self.selection()[0]"""
        if s := self.selection():
            return s[0]
        return ""

    def get_linear_iid_path_list(self, parent_iid: str = "") -> list[str]:
        """Return an unstructured list of child-iid_path's started from `start_id` (recursive)."""
        _list = list()

        def add(_iid=parent_iid):
            _list.append(_iid)
            children = self.get_children(_iid)
            for _iid in children:
                _list.append(_iid)
                add(_iid)

        add()
        return _list[1:]

    def set_selection(self, node: TreeNode) -> None:
        """self.selection_set(node.iid_path)"""
        self.selection_set(node.iid_path)

    def set_width(self, width: int, minwidth: int = None) -> None:
        """self.column("#0", width=width, minwidth=minwidth)"""
        if minwidth:
            self.column("#0", width=width, minwidth=minwidth)
        else:
            self.column("#0", width=width)


MAN_PAGE = (
    "Keybindings",
    """
· search_entry
    · "<F1>": open manual popup
    · "<F3>": confirm search pattern and go to next match
    · "<Shift-F3>": confirm search pattern and go to prev. match
    · "<Return>": confirm search pattern
    · "<Control-BackSpace>": delete search entry and matches
    · "<Down>": set focus to tree
    · ["<Control-l>": toggle load interface]
    · ["<Control-d>": toggle dump interface]
· expand_button
    · "<Button-1>": toggle recursive expand
    · "<Return>": toggle recursive expand
    · "<space>": toggle recursive expand
· tree 
    · "<Button-1>": toggle check
    · "<Double-Button-1>": toggle check
    · "<Double-Right>": recursive expand
    · "<Double-Left>": recursive collapse
    · "+": recursive expand
    · "-": recursive collapse
    · "<Return>": toggle check
    · "<space>": toggle check
    · "#": toggle check
    · "x": toggle recursive expand
    · "<F1>": open manual popup
    · "<Control-f>": enter search entry
    · "<F3>": next search match
    · "<Shift-F3>": prev. search match
    · ["<Control-l>": toggle load interface]
    · ["<Control-d>": toggle dump interface]
· [help_label] 
    · "<Button-1>": open manual popup
· _help_root
    · "<F1>": destroy manual popup
    · "<Escape>": destroy manual popup
""")


class SelectTreeWidget(ttk.Frame):
    """
    Add a search input and "expand-all" button with corresponding functionality to the top of the :class:`SelectTree`.

    [Optional] Add a Confirm and Cancel button at the bottom (without key bindings).

    [Optional] Add a text at the bottom and bind <click> to open the manual popup.

    [Optional] Add a dump and load interface.

    `ttk_styler` gets an instance of :class:`ttk.Style`.
        Since style configurations with more complex objects such as

        ``font = tk.font.Font()``

        ``font.configure(underline=True)``

        ``style.map('Treeview', font=[('selected', __nav_font)]])``

        apparently not effective if the objects are not saved,
        they should be returned in a dictionary (e.g., by ``return locals()``).

        Styles in use:
            - select.Treeview
            - search.TEntry
            - expand.TButton
            - help.TLabel
            - manual.TNotebook
            - manual.TFrame
            - manual.Vertical
            - manual.TLabel
            - confirm.TFrame
            - cancel.TButton
            - confirm.TButton

    `man_pages` is piped to :class:`ManWidget`.

    ````

    Keybindings:
        - search_entry
            - "<F1>": open manual popup
            - "<F3>": confirm search pattern and go to next match
            - "<Shift-F3>": confirm search pattern and go to prev. match
            - "<Return>": confirm search pattern
            - "<Control-BackSpace>": delete search entry and matches
            - "<Down>": set focus to tree
            - ["<Control-l>": toggle load interface]
            - ["<Control-d>": toggle dump interface]
        - expand_button
            - "<Button-1>": toggle recursive expand
            - "<Return>": toggle recursive expand
            - "<space>": toggle recursive expand
        - tree
            - "<Button-1>": toggle check
            - "<Double-Button-1>": toggle check
            - "<Double-Right>": recursive expand
            - "<Double-Left>": recursive collapse
            - "+": recursive expand
            - "-": recursive collapse
            - "<Return>": toggle check
            - "<space>": toggle check
            - "#": toggle check
            - "x": toggle recursive expand
            - "<F1>": open manual popup
            - "<Control-f>": enter search entry
            - "<F3>": next search match
            - "<Shift-F3>": prev. search match
            - ["<Control-l>": toggle load interface]
            - ["<Control-d>": toggle dump interface]
        - [help_label]
            - "<Button-1>": open manual popup
        - _help_root
            - "<F1>": destroy manual popup
            - "<Escape>": destroy manual popup
    """
    master: tk.Misc | None

    widget_frame: ttk.Frame
    tree: SelectTree
    search_entry: ttk.Entry
    expand_button: ttk.Button

    confirm_frame: ttk.Frame | None
    cancel_button: ttk.Button | None
    confirm_button: ttk.Button | None

    help_label: ttk.Label | None
    man_pages: Iterable[tuple[str, str]]
    man_title: str

    mode: Literal["multi", "single", "single entry", "single sector"]

    def __init__(
            self,
            master: tk.Misc | None,
            *structure: TreeNode,
            checked_iids: Iterable[TreeNode | str] = (),
            mode: Literal["multi", "single", "single entry", "single sector"],
            tags_config_update: TagsConfig = TagsConfig(
                match_entry=None,
                match_sector=None,
                match_hint_sector=None,
                match_hint_and_match_sector=None,
                check_entry=None,
                uncheck_entry=None,
                check_sector=None,
                uncheck_sector=None,
                ccstate_sector=None,
                type_entry=dict(),
                type_sector=dict(),
                type_top_sector=dict(),
                type_sub_sector=dict(),
            ),
            add_confirm_frame: bool = True,
            add_help_label: bool | str = "press <F1> for [ HELP ]",
            add_dump_and_load: bool = True,
            ttk_styler: Callable[[ttk.Style], dict] | None = None,
            man_pages: Iterable[tuple[str, str]] = (MAN_PAGE,),
            man_title: str = "[help] Tree Select"
    ):
        self.man_pages = man_pages
        self.man_title = man_title
        self.mode = mode
        if self.mode == "multi":

            def check(e, iid=None):
                if iid:
                    self.tree.toggle_check(iid_path=iid)
                elif self.tree.event_points_to(e, "image"):
                    self.tree.toggle_check(iid_path=self.tree.iid_path_by_event(e))

        elif self.mode == "single":

            def check(e, iid=None):
                if iid:
                    self.tree.toggle_single_check(iid_path=iid)
                elif self.tree.event_points_to(e, "image"):
                    self.tree.toggle_single_check(iid_path=self.tree.iid_path_by_event(e))

        elif self.mode == "single entry":

            def check(e, iid=None):
                if iid:
                    if iid not in self.tree.all_sector_iids:
                        self.tree.toggle_single_check(iid_path=iid)
                elif self.tree.event_points_to(e, "image"):
                    iid = self.tree.iid_path_by_event(e)
                    if iid not in self.tree.all_sector_iids:
                        self.tree.toggle_single_check(iid_path=iid)

        elif self.mode == "single sector":

            def check(e, iid=None):
                if iid:
                    if iid in self.tree.all_sector_iids:
                        self.tree.toggle_single_check(iid_path=iid)
                elif self.tree.event_points_to(e, "image"):
                    iid = self.tree.iid_path_by_event(e)
                    if iid in self.tree.all_sector_iids:
                        self.tree.toggle_single_check(iid_path=iid)

        else:
            raise ValueError(self.mode)

        self.toggle_check = check

        self.master = master
        ttk.Frame.__init__(self, master)
        self.widget_frame = ttk.Frame(self)

        _folder = str(Path(__file__).parent)

        self.tree = SelectTree(
            *structure,
            tags_config=TagsConfig(
                match_entry={'background': "#489F59", 'foreground': "black"},
                match_sector={'background': "#489F59", 'foreground': "black"},
                match_hint_sector={'background': "#F9F46E"},
                match_hint_and_match_sector={'background': "#70F05F"},
                check_entry=dict(image=tk.PhotoImage(file=_folder + "/dat/checkbox_checked18.png", master=self.widget_frame)),
                uncheck_entry=dict(image=tk.PhotoImage(file=_folder + "/dat/checkbox_unchecked18.png", master=self.widget_frame)),
                check_sector=dict(image=tk.PhotoImage(file=_folder + "/dat/checkbox_checked18.png", master=self.widget_frame)),
                uncheck_sector=dict(image=tk.PhotoImage(file=_folder + "/dat/checkbox_unchecked18.png", master=self.widget_frame)),
                ccstate_sector=dict(image=tk.PhotoImage(file=_folder + "/dat/checkbox_hover18.png", master=self.widget_frame)),
            ) | tags_config_update,
            master=self.widget_frame
        )
        for iid in checked_iids:

            if isinstance(iid, TreeNode):
                for _iid in iid.children_iid_paths_linear_iter():
                    self.tree.toggle_check(True, _iid)
            else:
                self.tree.toggle_check(True, iid)

        self.search_entry = ttk.Entry(
            master=self.widget_frame,
        )
        self.expand_button = ttk.Button(
            master=self.widget_frame,
            text="ᐅ",
            width=2,
        )

        if add_confirm_frame:
            self.confirm_frame = ttk.Frame(self)
            self.cancel_button = ttk.Button(self.confirm_frame, text="Cancel")
            self.confirm_button = ttk.Button(self.confirm_frame, text="Confirm")
            self.cancel_button.pack(side="left", expand=True)
            self.confirm_button.pack(side="left", expand=True)
            self.confirm_frame.grid(row=2, column=0, sticky=tk.NSEW)

            self.confirm_frame.configure(style="confirm.TFrame")
            self.cancel_button.configure(style="cancel.TButton")
            self.confirm_button.configure(style="confirm.TButton")
        else:
            self.confirm_frame = None
            self.cancel_button = None
            self.confirm_button = None

        if add_help_label:
            self.help_label = ttk.Label(self, text=(add_help_label if isinstance(add_help_label, str) else "press <F1> for [ HELP ]"))
            self.help_label.grid(row=3, column=0, columnspan=2, sticky=tk.NSEW)
            self.help_label.bind("<Button-1>", lambda _: self.help_popup())
            self.help_label.configure(style="help.TLabel")
        else:
            self.help_label = None

        self.search_entry.configure(style="search.TEntry")
        self.expand_button.configure(style="expand.TButton")
        self.tree.configure(style="select.Treeview")

        if ttk_styler is not None:
            gl = globals()
            gl |= {"." + k: v for k, v in ttk_styler(ttk.Style(master)).items()}

        self.tree.bind("<Button-1>", self.toggle_check, add=True)
        self.tree.bind("<Double-Button-1>", lambda e: (self.toggle_check(e, _iid) if (_iid := self.tree.iid_path_by_selected()) not in self.tree.all_sector_iids else None))
        self.tree.bind("<Double-Right>", lambda e: self.tree.toggle_recursive_expand(self.tree.iid_path_by_selected(), True))
        self.tree.bind("<Double-Left>", lambda e: self.tree.toggle_recursive_expand(self.tree.iid_path_by_selected(), False))
        self.tree.bind("+", lambda e: self.tree.toggle_recursive_expand(self.tree.iid_path_by_selected(), True))
        self.tree.bind("-", lambda e: self.tree.toggle_recursive_expand(self.tree.iid_path_by_selected(), False))
        self.tree.bind("<Return>", lambda e: (self.toggle_check(e, self.tree.iid_path_by_selected()) if e.state == 16 else None))
        self.tree.bind("<space>", lambda e: (self.toggle_check(e, self.tree.iid_path_by_selected()) if e.state == 16 else None))
        self.tree.bind("#", lambda e: self.toggle_check(e, self.tree.iid_path_by_selected()))

        self.tree.bind("x", lambda _: self.recursive_expand())

        self.tree.bind("<F1>", lambda _: self.help_popup())

        self.tree.bind("<Control-f>", lambda _: self.search_entry.focus_set())
        self.tree.bind("<F3>", lambda _: self.next_match(False))
        self.tree.bind("<Shift-F3>", lambda _: self.next_match(True))

        self.search_entry.bind("<F1>", lambda _: self.help_popup())

        self.search_entry.bind("<F3>", lambda _: (self.search(), self.next_match(False)))
        self.search_entry.bind("<Shift-F3>", lambda _: (self.search(), self.next_match(True)))

        self.search_entry.bind("<Return>", lambda _: self.search())
        self.search_entry.bind("<Control-BackSpace>", lambda _: self.delete_search())
        self.search_entry.bind("<Down>", lambda _: self.tree.focus_set())

        self.expand_button.bind("<Button-1>", lambda _: self.recursive_expand())
        self.expand_button.bind("<Return>", lambda _: self.recursive_expand())
        self.expand_button.bind("<space>", lambda _: self.recursive_expand())

        if add_dump_and_load:
            self.tree.bind("<Control-l>", lambda _: self.load())
            self.search_entry.bind("<Control-l>", lambda _: self.load())
            self.tree.bind("<Control-d>", lambda _: self.dump())
            self.search_entry.bind("<Control-d>", lambda _: self.dump())

        self.search_entry.grid(row=0, column=0, sticky=tk.NSEW)
        self.expand_button.grid(row=0, column=1, sticky=tk.NSEW)
        self.tree.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)
        self.widget_frame.grid(row=1, column=0)

    def resize(self, height: int, width: int) -> bool:
        """Return whether Tk is ready for sizing."""
        if self.confirm_frame:
            confirm_frame_geo = self.confirm_frame.winfo_geometry()
            if confirm_frame_geo.startswith("1x1"):
                return False
            height -= int(confirm_frame_geo.split("+")[0].split("x")[1]) // 10
            self.cancel_button.configure(width=width // 2 - 1)
            self.confirm_button.configure(width=width // 2 - 1)

        self.search_entry.configure(width=width - 2)
        self.tree.set_width(width)
        entry_height = int(self.search_entry.winfo_geometry().split("x")[1].split("+")[0])
        self.tree.configure(height=height - entry_height)
        return True

    def toggle_check(self, event, iid=None):
        ...

    def search(self):
        pattern = self.search_entry.get()
        if pattern:
            try:
                pattern = compile(pattern, IGNORECASE)
            except ReError:
                pattern = compile(escape(pattern), IGNORECASE)
            if self.tree.search(pattern):
                self.tree.toggle_recursive_expand(expand=False)
                self.tree.expand_for_match()
        else:
            self.tree.remove_match_tags()

    def delete_search(self):
        self.search_entry.delete(0, "end")
        self.tree.remove_match_tags()

    def recursive_expand(self):
        if self.tree.toggle_recursive_expand():
            self.expand_button.configure(text="ᐁ")
        else:
            self.expand_button.configure(text="ᐅ")

    def dump(self):
        if f := asksaveasfile(defaultextension=".json", filetypes=(("json", "*.json"),), initialdir=environ.get("HOME"), title="[dump] Tree Select"):
            with f:
                json.dump(self.tree.dump(), f)

    def load(self):
        if f := askopenfile(defaultextension=".json", filetypes=(("json", "*.json"),), initialdir=environ.get("HOME"), title="[load] Tree Select"):
            with f:
                self.tree.load(tuple(TreeNode.from_dict(d) for d in TreeNode.from_dict(json.load(f))))

    _match_end__reverse_mode = [False, False]

    def next_match(
            self, reverse: bool
    ):
        if to_begin := (self._match_end__reverse_mode[0] and reverse == self._match_end__reverse_mode[1]):
            self._match_end__reverse_mode[0] = False
        if m := self.tree.selection_to_next_match(
                reverse=reverse,
                back_to_begin=to_begin,
        ):
            self.tree.focus_set()
        self._match_end__reverse_mode[0], self._match_end__reverse_mode[1] = m is None, reverse

    _help_root: tk.Toplevel | None = None

    def help_popup(self):
        if self._help_root is not None:
            self._help_root.attributes('-topmost', True)
            self._help_root.focus_force()
            self._help_root.update_idletasks()
            self._help_root.attributes('-topmost', False)
        else:
            def _help_exit(*_):
                self._help_root.destroy()
                self._help_root = None

            self._help_root = tk.Toplevel(self.master)
            self._help_root.title(self.man_title)
            self._help_root.bind("<F1>", _help_exit)
            self._help_root.bind("<Escape>", _help_exit)
            self._help_root.protocol("WM_DELETE_WINDOW", _help_exit)
            ManWidget(
                self._help_root,
                *self.man_pages,
            ).pack(expand=True, fill=tk.BOTH)
