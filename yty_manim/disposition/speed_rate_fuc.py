# rainbow_yu manim_extend.disposition.speed_rate_func 🐋✨

def slow_then_fast(i):
    pass

def split_speed(
        i,
        lower_speed,
        upper_speed,
        split_line
):
    """
    分界线速度
    :param i: 位置
    :param lower_speed: 较慢的速度
    :param upper_speed: 较快的速度
    :param split_line: 分界线
    :return: speed
    """
    return lower_speed if i <= split_line else upper_speed
