# rainbow_yu manim_extend.disposition.fonts_and_colors 🐋✨

from manim import *

# 字体列表
text_font = [
    '汉仪中圆简',
    '时尚中黑简体',
]

# 渐变字典
gradient_dict = dict(
    rainbow_color=[RED, ORANGE, YELLOW, GREEN, TEAL, BLUE, PURPLE],
    rainbow_color_dark=[RED_D, ORANGE, YELLOW_E, GREEN_D, TEAL_D, BLUE_D, PURPLE_D],
    rainbow_color_reverse=[PURPLE, BLUE, TEAL, GREEN, YELLOW, ORANGE, RED],
    favourite=["#84fab0", "#8fd3f4"],
    Rainy_Ashville=["#fbc2eb", "#a6c1ee"],
    Sunny_Morning=["#f6d365", "#fda085"],
    Sunny_Morning_light=["#ffffc5", "#fff0d5"],
    Tempting_Azure=["#84fab0", "#8fd3f4"],
    Tempting_Azure_dark=["#64C883", "#6297B5"],
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
    "default_type": {
        "side_length": 1,
        "fill_color": BLUE,
        "fill_opacity": 0.5,
        "stroke_opacity": 0.8,
        "color": BLUE
    },

    "default_st_type": {
        "side_length": 1,
        "fill_color": BLUE,
        "fill_opacity": 0.5,
        "stroke_opacity": 0.8,
        "color": BLUE
    },

    "default_pointer_type":{
        "fill_color": YELLOW,
        "fill_opacity": 0.5,
        "stroke_opacity": 0.8,
        "color": YELLOW
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


# ── CS2 / 冲击波 / 预烘焙相关默认颜色与布局参数 ───────────────

def safe_ui_font() -> str:
    """优先选用系统可用的中文 UI 字体。"""
    try:
        from manim.utils.fonts import get_available_fonts

        available = set(get_available_fonts())
        for name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", *text_font, "Sans"):
            if name in available:
                return name
    except Exception:
        pass
    return "Sans"


UI_FONT = safe_ui_font()
CODE_FONT = "Consolas"

# ── 三维竞技场 Arena3D ───────────────────────────────────────
cs2_arena_3d = dict(
    BG="#07070c",
    FLOOR="#243044",
    FLOOR_SIDE="#1c2636",
    FLOOR_EDGE="#3a4860",
    WALL="#5a6578",
    WALL_SIDE="#4a5568",
    WALL_TOP="#8b97ab",
    ACCENT_OLD="#ff4d4d",
    ACCENT_OLD_GLOW="#ff8080",
    ACCENT_NEW="#3de0c8",
    ACCENT_NEW_HOT="#ff5c4d",
    ACCENT_NEW_MID="#f0a040",
    BOMB_GLOW="#ff3366",
    SAFE="#5eead4",
    TITLE_C="#f0f4ff",
    CELL=0.58,
    WALL_H=1.05,
    FLOOR_H=0.14,
    TILE_SCALE=0.94,
    WALL_SCALE=0.98,
)

# ── 二维寻路 GridMap2D ───────────────────────────────────────
cs2_pathfinding = dict(
    C_BG="#06080f",
    C_FLOOR="#1c2838",
    C_WALL="#2a3548",
    C_WALL_EDGE="#3d4d66",
    C_START="#ff4d6d",
    C_GOAL="#5eead4",
    C_PATH="#fff7ed",
    C_PANEL="#0e1420",
    C_PANEL_EDGE="#2a3a55",
    C_TITLE="#eef2ff",
    C_SUB="#94a3b8",
    C_VIS_COOL="#3de0c8",
    C_VIS_MID="#f0c040",
    C_VIS_HOT="#ff6b4a",
    C_EUCL="#ff5c7a",
    CELL_2D=0.52,
    CELL_GAP=0.06,
    MAP_SCALE=0.90,
    PANEL_BUFF=0.55,
    Z_MAP=0,
    Z_PANEL=2,
    Z_METRICS=7,
    Z_PATH=8,
    Z_MARKERS=10,
    # MAP_SHIFT 含 LEFT/UP，在模块内用向量装配
    MAP_SHIFT_LEFT=2.75,
    MAP_SHIFT_UP=0.05,
)

# ── 预烘焙伤害教学 ───────────────────────────────────────────
cs2_damage = dict(
    C_BG="#0a0c12",
    C_TITLE="#f1f5ff",
    C_SUB="#a8b4c8",
    C_MUTED="#6b778c",
    C_PANEL="#101621",
    C_PANEL_EDGE="#2a3548",
    C_MAP="#1a2230",
    C_WALL="#5a6578",
    C_WOOD="#a67c52",
    C_BRICK="#6d5a4e",
    C_BLAST="#ff6b3d",
    C_BLAST_GLOW="#feac5e",
    C_HEAT_HI="#ffe566",
    C_HEAT_MID="#ff5a3c",
    C_HEAT_LO="#7a1f1f",
    C_HP="#3dd68c",
    C_HP_PREVIEW="#ff4d5a",
    C_PLAYER_A="#4bc0c8",
    C_PLAYER_B="#a78bfa",
    C_PLAYER_C="#fbbf24",
    C_ACCENT="#3de0c8",
    C_WARN="#f59e0b",
    MAP_W=8.6,
    MAP_H=5.0,
    MAP_ORIGIN=(-4.3, -1.6, 0.0),
    GRID_NX=16,
    GRID_NY=10,
    D_MAX=500.0,
    RADIUS=4.2,
    HP_MAX=100.0,
    HP_START=84.0,
    MAT_OPEN=1.00,
    MAT_WOOD=0.45,
    MAT_BRICK=0.15,
    MAT_CONCRETE=0.00,
)

# ── 三维伤害丘 ───────────────────────────────────────────────
cs2_damage_hill = dict(
    C_BG="#07090f",
    C_DOT="#ffffff",
    C_TRAIL="#ffffff",
    C_CORE="#ff2d55",
    C_LETHAL="#ef4444",
    X_MIN=-4.4,
    X_MAX=4.4,
    Y_MIN=-3.6,
    Y_MAX=3.6,
    R_LETHAL=1.05,
    R_BLAST=4.2,
    Z_SCALE=2.7,
    # (t, hex) 峰顶红 → 山脚深蓝
    HEIGHT_STOPS=(
        (0.00, "#1e3a8a"),
        (0.18, "#0ea5e9"),
        (0.36, "#14b8a6"),
        (0.52, "#22c55e"),
        (0.68, "#eab308"),
        (0.82, "#f97316"),
        (1.00, "#ef4444"),
    ),
)

# ── 地图冲击波热力（Mirage / MapBundle 共用波色）────────────
cs2_map_heat = dict(
    C_WAVE_HOT="#ff6b35",
    C_WAVE_MID="#f7c548",
    C_WAVE_COOL="#4ecdc4",
    C_WALK="#1a2332",
    C_FLOOR_EDGE="#4a4a55",
    C_GLOW="#ff3366",
    MAP_W=12.0,
    MAP_H=9.0,
    CELL_GAP=0.04,
)

cs2_mirage_map = dict(
    **cs2_map_heat,
    C_BG="#060608",
    WAVE_UPSAMPLE=2,
    MAX_CONTOUR_PTS=80,
    RADIUS_QUANT=0.65,
)

cs2_bundle_map = dict(
    **cs2_map_heat,
    C_BG="#121216",
)

# 物理/数据侧常量（非颜色，但与 CS2 地图默认配置同源）
cs2_map_physics = dict(
    CELL_METERS=0.625,
    WAVE_SPEED_M_S=27.5,
    GRID_W=128,
    GRID_H=96,
    RADAR_SIZE=1024,
)


"""
                          __                                                    
               __        /\ \                                                   
 _ __    __   /\_\    ___\ \ \____    ___   __  __  __          __  __  __  __  
/\`'__\/'__`\ \/\ \ /' _ `\ \ '__`\  / __`\/\ \/\ \/\ \        /\ \/\ \/\ \/\ \ 
\ \ \//\ \L\.\_\ \ \/\ \/\ \ \ \L\ \/\ \L\ \ \ \_/ \_/ \       \ \ \_\ \ \ \_\ \
 \ \_\\ \__/.\_\\ \_\ \_\ \_\ \_,__/\ \____/\ \___x___/'        \/`____ \ \____/
  \/_/ \/__/\/_/ \/_/\/_/\/_/\/___/  \/___/  \/__//__/    _______`/___/> \/___/ 
                                                         /\______\  /\___/      
                                                         \/______/  \/__/       

 ______     _   __   __   __   __     
/\  ___\  /' \ /\ \ /\ \ /\ \ /\ \    
\ \ \__/ /\_, \\ `\`\/'/'\ `\`\/'/'   
 \ \___``\/_/\ \`\/ > <   `\/ > <     
  \/\ \L\ \ \ \ \  \/'/\`\   \/'/\`\  
   \ \____/  \ \_\ /\_\\ \_\ /\_\\ \_\
    \/___/    \/_/ \/_/ \/_/ \/_/ \/_/
                                                                       
"""
