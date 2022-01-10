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


from tkinter import Text
from tkinter import END
from re import Pattern, search, finditer


__all__ = ["TextHighlighter"]


class TextHighlighter:

    def __init__(self,
                 text: Text,
                 main_config: dict[Pattern]=False,
                 first_clause: dict[Pattern]=False,
                 return_clause: set[Pattern]=False,
                 sub_loop: list[dict[Pattern], set[Pattern], dict[Pattern]]=False,
                 strict_sub_loop: list[dict[Pattern], set[Pattern], dict[Pattern]]=False,
                 at_call: dict[Pattern]=None,
                 ):

        """
        A simple highlighter for the tk text widget

        *Configuration attribute format = {Pattern : tag_config-kwarg, ...}

        **Loops configurations = [first_clauses=*Configuration, break_clauses=set(Pattern), loop_configs=*Configuration]

        The process starts with execution of `self.highlight'.
        In case multiple highlighters are to be used for different sectors, `self.highlight'
        returns the line number of the last match, and the process can be aborted earlier by the `return_clause'.

        :param text: tk-text
        :param main_config: Main configuration, a library whose keys are regular expressions and whose values are a kwargs for the tag_config method.
        :param first_clause: One of his *Configurations must first apply.
        :param return_clause: If one of the patterns is matched, it is aborted and the line of the last match is returned.
        :param sub_loop: Configurations for a special loop, the main configurations are still respected.
        :param strict_sub_loop: Strict loop, do not pay attention to the main configurations. But those of the parent loop when nested.
        :param at_call: (Global) Execute a function if the pattern matches. The function gets the line, the line number and the re.match.  If by this TextHighlighting itself is changed, the RuntimeError is caught and executed again.
        """

        self.text: Text = text
        self.config: dict[Pattern] = (main_config if main_config else {})
        self.first_clause: dict[Pattern] = first_clause
        self.return_clause: set[Pattern] = (return_clause if return_clause else set())
        self.sub_loop: list[dict[Pattern], set[Pattern], dict[Pattern]] = (sub_loop if sub_loop else [{}, set(), {}])
        self.strict_sub_loop: list[dict[Pattern], set[Pattern], dict[Pattern]] = (strict_sub_loop if strict_sub_loop else [{}, set(), {}])
        self.at_call = (at_call if at_call else {})

        self.alltags: set = set()
        self.sub_tags: dict[str, set] = dict()
        self.ssub_tags: dict[str, set] = dict()

        self._read_start = "1.0"

    def _add_tag(self, _lineno, _match, _kwarg):
        start = "%d.%d" % (_lineno, _match.start())
        end = "%d.%d" % (_lineno, _match.end())
        _id = "%s:%s::%s" % (start, end, _match.group())
        self.text.tag_add(_id, start, end)
        self.text.tag_config(_id, **_kwarg)
        return _id

    def highlight(self, flush: bool = False, read_start: str = "1.0", note_first_clause: bool = True) -> int:

        """
        :param flush: delete all tags
        :param read_start: from there shall be read (line.column)
        :param note_first_clause: note first_clause
        :return: int: line number of the last match
        """

        if flush and self.alltags:
            self.text.tag_delete(*self.alltags)
            self.alltags: set = set()
            self.sub_tags: dict[str, set] = dict()
            self.ssub_tags: dict[str, set] = dict()

        _config = (self.first_clause if self.first_clause and note_first_clause else self.config)
        inside_sub_loop = False
        inside_ssub_loop = False

        self._read_start = read_start

        for n, ln in enumerate(self.text.get(read_start, END).splitlines(), int(search("\d+", read_start).group())):

            for p in self.return_clause:
                if search(p, ln):
                    return int(self._read_start.split('.')[0])

            try:
                for p in self.at_call:
                    if m := search(p, ln):
                        self.at_call[p].__call__(ln, n, m)
            except RuntimeError:
                for p in self.at_call:
                    if m := search(p, ln):
                        self.at_call[p].__call__(ln, n, m)

            if not inside_sub_loop:
                for p in self.sub_loop[0]:
                    for m in finditer(p, ln):
                        _id = self._add_tag(n, m, self.sub_loop[0][p])
                        self.alltags.add(_id)
                        self.sub_tags[_id] = set()
                        inside_sub_loop = _id

            else:
                for p in self.sub_loop[1]:
                    if search(p, ln):
                        self._read_start = "%d.0" % n
                        return self.highlight(False, "%d.0" % n, False)

                if inside_sub_loop:
                    for p in self.sub_loop[2]:
                        for m in finditer(p, ln):
                            _id = self._add_tag(n, m, self.sub_loop[2][p])
                            self.alltags.add(_id)
                            self.sub_tags[inside_sub_loop].add(_id)

            if not inside_ssub_loop:
                for p in self.strict_sub_loop[0]:
                    for m in finditer(p, ln):
                        _id = self._add_tag(n, m, self.strict_sub_loop[0][p])
                        self.alltags.add(_id)
                        self.ssub_tags[_id] = set()
                        inside_ssub_loop = _id

                if inside_ssub_loop:
                    continue

            else:
                for p in self.strict_sub_loop[1]:
                    if search(p, ln):
                        self._read_start = "%d.0" % n
                        return self.highlight(False, "%d.0" % n, False)

                if inside_ssub_loop:
                    for p in self.strict_sub_loop[2]:
                        for m in finditer(p, ln):
                            _id = self._add_tag(n, m, self.strict_sub_loop[2][p])
                            self.alltags.add(_id)
                            self.ssub_tags[inside_ssub_loop].add(_id)
                    continue

            for p in _config:
                matched = False
                for m in finditer(p, ln):
                    matched = True
                    _id = self._add_tag(n, m, _config[p])
                    self.alltags.add(_id)
                if matched:
                    _config = self.config
                    self._read_start = "%d.0" % n

        return int(self._read_start.split('.')[0])

if __name__ == "__main__":
    from tkinter import Tk
    from tkinter.scrolledtext import ScrolledText
    from re import compile
    from tkinter.font import Font, nametofont

    CONTENT = """

                                        Python Program for Fibonacci numbers             

    Difficulty Level : Easy
    Last Updated : 17 Dec, 2021

The Fibonacci numbers are the numbers in the following integer sequence.
0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, ……..
In mathematical terms, the sequence Fn of Fibonacci numbers is defined by the recurrence relation

     Fn = Fn-1 + Fn-2

with seed values

     F0 = 0 and F1 = 1.

Method 2 ( Use Dynamic Programming ) :

    # Function for nth fibonacci
    # number - Dynamic Programming
    # Taking 1st two fibonacci numbers as 0 and 1
    FibArray = [0, 1]

    def fibonacci(n):

        # Check is n is less                                   ;
        # than 0                                               ;
        if n <= 0:                                             ;
            print("Incorrect input")                           ;

        # Check is n is less                                   ;
        # than len(FibArray)                                   ;
        elif n <= len(FibArray):                               ;
            return FibArray[n - 1]                             ;
        else:                                                  ;
            temp_fib = fibonacci(n - 1) +                      ;
                        fibonacci(n - 2)                       ;
            FibArray.append(temp_fib)                          ;
            return temp_fib                                    ;

    # Driver Program
    print(fibonacci(9))

    # This code is contributed by Saket Modi

Method 3 ( Space Optimized):

    # Function for nth fibonacci
    # number - Space Optimisation
    # Taking 1st two fibonacci numbers as 0 and 1

    def fibonacci(n):
        a = 0                                                  ;
        b = 1                                                  ;

        # Check is n is less                                   ;
        # than 0                                               ;
        if n < 0:                                              ;
            print("Incorrect input")                           ;

        # Check is n is equal                                  ;
        # to 0                                                 ;
        elif n == 0:                                           ;
            return 0                                           ;

        # Check if n is equal to 1                             ;
        elif n == 1:                                           ;
            return b                                           ;
        else:                                                  ;
            for i in range(1, n):                              ;
                c = a + b                                      ;
                a = b                                          ;
                b = c                                          ;
            return b                                           ;

    # Driver Program
    print(fibonacci(9))

    # This code is contributed by Saket Modi
    # Then corrected and improved by Himanshu Kanojiya

Please refer complete article on Program for Fibonacci numbers for more details! 
https://www.geeksforgeeks.org/program-for-nth-fibonacci-number/

-------------------------------------------------------------------------------------------

Article Contributed By : GeeksforGeeks

Improved By :

    grohith70
    himanshukanojiya
    adnanirshad158
    akshaysingh98088
    simranarora5sos

[¹] https://www.geeksforgeeks.org/python-program-for-program-for-fibonacci-numbers-2/

-------------------------------------------------------------------------------------------
"""

    t = Tk()
    _family = {"family": nametofont("TkFixedFont").cget("family")}
    font = Font(size=10, **_family)
    text = ScrolledText(t, width=120, height=50, font=font)
    text.pack(fill="both")
    text.insert("1.0", CONTENT)

    bold12 = Font(weight="bold", size=12, **_family)
    bold10 = Font(weight="bold", size=10, **_family)
    underline12 = Font(underline=True, size=12, **_family)
    underline10 = Font(underline=True, size=10, **_family)

    kforeground = 'foreground'
    kbackground = 'background'
    kfont = 'font'

    last_match = TextHighlighter(
        text,
        main_config={
            compile("[fF]ibonacci"): {
                kforeground: "red"
            },
            compile("(?<= {5}).*"): {
                kbackground : "black",
                kforeground : "white"
            },
            compile("https?://.*"): {
                kforeground : "green"
            }
        },
        first_clause={
            compile("\s\w.*\w\s"): {
                kforeground: "green",
                kfont: underline12
            }
        },
        sub_loop=[
            {
                compile("^Method \d"): {
                    kforeground: "blue",
                    kfont: bold12
                }
            },
            {compile("^\S")},
            {
                compile("^\s*\w.*"): {
                    kforeground : "magenta"
                },
                compile("(?<= def )\w+"): {
                    kfont: bold10,
                    kforeground : "black"
                }
            }
        ],
        strict_sub_loop=[
            {
                compile("(?<= )def(?= \w.+:)"): {
                    kforeground : "orange",
                    kfont : bold10
                }
            },
            {compile("^\S")},
            {
                compile(".*"): {
                    kforeground : "black"
                },
                compile("(if|elif|else|for|return)"): {
                    kforeground : "orange",
                    kfont : bold10
                },
                compile("print"): {
                    kforeground: "cyan",
                    kfont: bold10
                },
                compile("\d+"): {
                    kforeground: "blue"
                },
                compile(".*\S.*(?=;)"): {
                    kbackground: "lightgrey"
                },
                compile(";"): {
                    kforeground: "white"
                }
            }
        ],
        #return_clause={compile("^-{10}"),}
    ).highlight(True)

    text.insert(f"{last_match}.1000", f"        <------   [ {last_match=} ]")

    t.mainloop()

