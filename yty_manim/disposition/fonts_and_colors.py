# rainbow_yu manim_extend.disposition.fonts_and_colors 🐋✨

from manim import *

# 字体列表
text_font = [
    '汉仪中圆简'
    '时尚中黑简体',
]

# 渐变字典
gradient_dict = dict(
    favourite=["#84fab0", "#8fd3f4"],
    Rainy_Ashville=["#fbc2eb", "#a6c1ee"],
    Sunny_Morning=["#f6d365", "#fda085"],
    Sunny_Morning_light=["#ffffc5", "#fff0d5"],
    Tempting_Azure=["#84fab0", "#8fd3f4"],
    Child_Care=["#f794a4", "#fdd6bd"],
    blue_green_dark=["#051937", "#004d7a", "#008793", "#00bf72", "#a8eb12"],
    red_purple_blue=["#12c2e9", "#c471ed", "#f64f59"],
    red_blue_green=["#D16BA5", "#86A8E7", "#5FFBF1"],
    red_purple_blue_dark=["#aa4b6b", "#6b6b83", "#3b8d99"],
    red_yellow_green_light=["#f7797d", "#fbd786", "#c6ffdd"],
    orange_pink_blue=["#feac5e", "#c779d0", "#4bc0c8"],
    red_green=["#D16BA5", "#5FFBF1"],
    red_blue=["#D16BA5", "#86A8E7"],
    blue_green=["#86A8E7", "#5FFBF1"],
    purple_light=["#654ea3", "#eaafc8"],
    rice_white=["#ffefba", "#ffffff"],
    blue_gray=["#c9d6ff", "#e2e2e2"],
    pink_orange=["#ffafbd", "#ffc3a0"])

# 形状字典
typedict = {
    "blue_type": {
        "side_length": 1,
        "fill_color": BLUE,
        "fill_opacity": 0.5,
        "stroke_opacity": 0.8,
        "color": BLUE
    },

    "red_type": {
        "side_length": 1,
        "fill_color": RED,
        "fill_opacity": 0.5,
        "stroke_opacity": 0.8,
        "color": RED
    },

    "yellow_type": {
        "side_length": 1,
        "fill_color": YELLOW,
        "fill_opacity": 0.5,
        "stroke_opacity": 0.8,
        "color": YELLOW
    },

    "green_type": {
        "side_length": 1,
        "fill_color": GREEN,
        "fill_opacity": 0.5,
        "stroke_opacity": 0.8,
        "color": GREEN
    },

    "lightblue_type": {
        "side_length": 1,
        "fill_color": BLUE_A,
        "fill_opacity": 0.5,
        "stroke_opacity": 0.8,
        "color": BLUE_A
    },

    "rec_yellow": {
        "width": 1,
        "height": 2,
        "fill_opacity": 0,
        "stroke_opacity": 1,
        "color": YELLOW
    },

    "rec_yellow3": {
        "width": 1,
        "height": 3,
        "fill_opacity": 0,
        "stroke_opacity": 1,
        "color": YELLOW
    },

    "broad_cast": {
        'big_radius': 5,
        'n_circles': 8,
        'lag_ratio': 0.1,
        'color': YELLOW
    }
}


"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
\\                 _           _                                                  \\
\\  _ __    __ _  (_)  _ __   | |__     ___   __      __          _   _   _   _   \\
\\ | '__|  / _` | | | | '_ \  | '_ \   / _ \  \ \ /\ / /         | | | | | | | |  \\
\\ | |    | (_| | | | | | | | | |_) | | (_) |  \ V  V /          | |_| | | |_| |  \\
\\ |_|     \__,_| |_| |_| |_| |_.__/   \___/    \_/\_/    _____   \__, |  \__,_|  \\
\\                                                       |_____|  |___/           \\
\\                                                                                \\
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
"""
