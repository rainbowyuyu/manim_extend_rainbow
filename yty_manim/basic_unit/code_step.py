# rainbow_yu manim_extend.basic_unit.code_step 🐋✨
# code on step

from manim import *

class CodeStep(Code):
    """
    code which can write use auto run_time paired with code length

    Examples
    ------

    >>> class CodeShow(Scene):
    >>>     c1 = CodeStep("aaa")
    >>>     for i in range(len(c1[2])):
    >>>         c1.write_code(self,1,is_auto_runtime=True)
    >>>         self.wait(10)

    """
    def __init__(
            self,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.lines = 0

    def write_code(
            self,
            scene,
            lines : int,
            is_auto_runtime : bool = True,
            **kwargs
    ):
        """
        Write the code line to the screen.
        :param scene: manim.scene.Scene
        :param lines: line number
        :param is_auto_runtime: use automatic runtime
        :return: self
        """
        end_line = self.lines + lines
        if is_auto_runtime:
            scene.play(Write(self[2][self.lines:end_line]),run_time = self.auto_runtime(lines), **kwargs)
        else:
            scene.play(Write(self[2][self.lines:end_line]), **kwargs)
        self.lines += lines
        return self

    def auto_runtime(self, lines):
        """
        auto write code runtime
        :param lines: line number
        :return: time
        """
        total_length = 0
        for i in range(self.lines,self.lines+lines):
            total_length += len(self[2][i])
        if total_length == 0:
            total_length = 1.5
        return total_length / 15