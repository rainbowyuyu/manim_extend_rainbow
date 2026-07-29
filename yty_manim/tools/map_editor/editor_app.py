# rainbow_yu — CS2-grade map editor with radar import, zoom/pan, precision tools

from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk

import numpy as np
from PIL import Image, ImageDraw, ImageTk

from yty_manim.tools.map_editor.editor_tools import (
    fill_rect,
    fill_region,
    is_floor_cell,
    is_obstacle_cell,
    nearest_marker,
    pick_cell_color,
    restore,
    snapshot,
    stamp_box,
    stamp_brush,
    stamp_line,
)
from yty_manim.tools.map_editor.map_bundle import (
    DEFAULT_BG_RGB,
    DEFAULT_FLOOR_RGB,
    DEFAULT_OBSTACLE_RGB,
    ExplosionSource,
    MapBundle,
    MapMarker,
    default_maps_dir,
)
from yty_manim.tools.map_editor.map_radar_import import import_from_radar_image, import_mirage_radar, mirage_radar_path

TOOLS = (
    ("paint", "画笔 B", "绘制可走地板"),
    ("obstacle", "障碍 O", "绘制墙体/不可走"),
    ("eraser", "橡皮 E", "擦除为地板"),
    ("flood", "填充 F", "区域填充"),
    ("line", "直线 L", "拖拽画线"),
    ("rect", "矩形 R", "拖拽画矩形"),
    ("eyedropper", "吸管 I", "吸取颜色"),
    ("explosion", "爆炸源 C", "放置 C4"),
    ("text", "标记 M", "文字标记"),
    ("move", "移动 V", "拖动标记点"),
    ("box", "箱子 P", "放置方形障碍预设"),
)

CS2_MARKERS = (
    ("A 包点", "#ff6600", "bomb"),
    ("B 包点", "#cc5555", "marker"),
    ("链接", "#66ccff", "marker"),
    ("Jungle", "#66ff99", "marker"),
    ("CT 家", "#6699ff", "marker"),
    ("T 家", "#ffcc44", "marker"),
)

COLOR_PRESETS = (
    ("地板灰", "#48484e"),
    ("A区红", "#8f3f3f"),
    ("B区红", "#7a3535"),
    ("CT蓝", "#3f668f"),
    ("T黄", "#b8a452"),
    ("走廊", "#5a5a62"),
)

OBSTACLE_PRESETS = (
    ("木箱", "#4a4038"),
    ("铁箱", "#52565c"),
    ("沙袋", "#6a5a42"),
    ("墙体", "#2a2624"),
    ("护栏", "#3d4a55"),
)

BOX_PRESETS = (
    ("小箱 2×2", 2, 2),
    ("箱 3×3", 3, 3),
    ("大箱 5×5", 5, 5),
    ("条箱 2×4", 2, 4),
    ("墙条 1×8", 1, 8),
)

LAYER_MODES = (
    ("all", "全部"),
    ("floor", "仅地图"),
    ("obstacle", "仅障碍"),
)

TOOL_GRID = (
    ("paint", "画笔", "B"),
    ("obstacle", "障碍", "O"),
    ("eraser", "橡皮", "E"),
    ("flood", "填充", "F"),
    ("line", "直线", "L"),
    ("rect", "矩形", "R"),
    ("box", "箱子", "P"),
    ("eyedropper", "吸管", "I"),
    ("explosion", "C4", "C"),
    ("text", "标记", "M"),
    ("move", "移动", "V"),
)


class MapEditorApp(tk.Tk):
    def __init__(self, bundle: MapBundle | None = None):
        super().__init__()
        self.title("Manim 地图编辑器 · CS2 Mirage")
        self.geometry("1440x900")
        self.minsize(1100, 700)

        self.bundle = bundle or MapBundle.blank("untitled")
        self.bundle_path: Path | None = None
        self.brush_size = 2
        self.brush_color = "#48484e"
        self._brush_rgb = DEFAULT_FLOOR_RGB
        self.obstacle_color = "#4a4038"
        self._obstacle_rgb = DEFAULT_OBSTACLE_RGB
        self._box_w, self._box_h = 3, 3
        self._alt_key_held = False
        self._mouse_xy = (0, 0)
        self._brush_resize_active = False
        self._brush_resize_origin_x = 0
        self._brush_resize_origin_size = 2
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.show_grid = True
        self.show_reference = False
        self.layer_mode = "all"
        self.show_markers_layer = True
        self.ref_opacity = 0.45
        self._reference_rgb: np.ndarray | None = None
        self._reference_path: Path | None = None

        self._dragging = False
        self._panning = False
        self._pan_anchor = (0, 0)
        self._stroke_start: tuple[int, int] | None = None
        self._last_ij: tuple[int, int] | None = None
        self._move_target: ExplosionSource | MapMarker | None = None
        self._photo: ImageTk.PhotoImage | None = None
        self._refresh_scheduled = False
        self._selected_source_id: str | None = (
            self.bundle.explosion_sources[0].id if self.bundle.explosion_sources else None
        )

        self._undo: list = []
        self._redo: list = []
        self._tool_buttons: dict[str, tk.Button] = {}
        self._layer_buttons: dict[str, tk.Button] = {}
        self._header_layer_buttons: dict[str, tk.Button] = {}
        self._push_undo()

        self._build_menubar()
        self._build_ui()
        self._bind_keys()
        self._refresh_canvas()
        self._refresh_lists()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # --- UI -----------------------------------------------------------------

    def _build_menubar(self) -> None:
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_m)
        for label, cmd in (
            ("新建", self._new_map),
            ("打开", self._open_map),
            ("保存", self._save_map),
            ("另存为", self._save_as),
            ("---", None),
            ("从雷达图导入...", self._import_radar_image),
            ("一键 Mirage 雷达", self._import_mirage_radar),
            ("---", None),
            ("Manim 预览", self._preview_manim),
        ):
            if label == "---":
                file_m.add_separator()
            else:
                file_m.add_command(label=label, command=cmd)

        edit_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_m)
        edit_m.add_command(label="撤销 Ctrl+Z", command=self._undo_action)
        edit_m.add_command(label="重做 Ctrl+Y", command=self._redo_action)

        view_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_m)
        view_m.add_command(label="放大 +", command=lambda: self._zoom_by(1.15))
        view_m.add_command(label="缩小 -", command=lambda: self._zoom_by(1 / 1.15))
        view_m.add_command(label="重置视图 0", command=self._reset_view)
        view_m.add_command(label="切换网格 G", command=self._toggle_grid)
        view_m.add_separator()
        for mode, label in LAYER_MODES:
            view_m.add_command(label=f"图层: {label}", command=lambda m=mode: self._set_layer_mode(m))

    def _set_layer_mode(self, mode: str) -> None:
        self.layer_mode = mode
        self._sync_layer_buttons()
        self._refresh_canvas()
        labels = dict(LAYER_MODES)
        self.status_var.set(f"图层: {labels.get(mode, mode)}")

    def _sync_layer_buttons(self) -> None:
        for mode, btn in self._layer_buttons.items():
            active = mode == self.layer_mode
            btn.config(
                relief=tk.SUNKEN if active else tk.RAISED,
                bg="#2d6a9f" if active else "#2a2a32",
                fg="white",
            )
        for mode, btn in self._header_layer_buttons.items():
            active = mode == self.layer_mode
            btn.config(
                relief=tk.SUNKEN if active else tk.RAISED,
                bg="#2d6a9f" if active else "#2a2a32",
                fg="white",
            )

    def _sync_tool_buttons(self) -> None:
        cur = self.tool_var.get()
        for tid, btn in self._tool_buttons.items():
            active = tid == cur
            btn.config(
                relief=tk.SUNKEN if active else tk.RAISED,
                bg="#3d6b8e" if active else "#2e2e36",
                fg="white",
            )

    def _toggle_grid(self) -> None:
        self.show_grid = not self.show_grid
        self._refresh_canvas()
        self.status_var.set("网格 " + ("开" if self.show_grid else "关"))

    def _build_ui(self) -> None:
        root = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        root.pack(fill=tk.BOTH, expand=True)

        left_wrap = ttk.Frame(root, width=300)
        right = ttk.Frame(root)
        root.add(left_wrap, weight=0)
        root.add(right, weight=1)

        left_canvas = tk.Canvas(left_wrap, width=300, highlightthickness=0, bg="#1a1a1e")
        left_scroll = ttk.Scrollbar(left_wrap, orient=tk.VERTICAL, command=left_canvas.yview)
        self._left_panel = ttk.Frame(left_canvas)
        self._left_panel.bind(
            "<Configure>",
            lambda _e: left_canvas.configure(scrollregion=left_canvas.bbox("all")),
        )
        left_canvas.create_window((0, 0), window=self._left_panel, anchor=tk.NW, width=288)
        left_canvas.configure(yscrollcommand=left_scroll.set)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def _on_mousewheel(event):
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        left_canvas.bind("<Enter>", lambda _e: left_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        left_canvas.bind("<Leave>", lambda _e: left_canvas.unbind_all("<MouseWheel>"))

        self._build_toolbar(self._left_panel)
        self._build_canvas_area(right)
        self._build_status_bar()

    def _build_toolbar(self, parent: ttk.Frame) -> None:
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        tab_tools = ttk.Frame(notebook)
        tab_brush = ttk.Frame(notebook)
        tab_objects = ttk.Frame(notebook)
        notebook.add(tab_tools, text="工具")
        notebook.add(tab_brush, text="笔刷")
        notebook.add(tab_objects, text="对象")

        layer_frame = ttk.LabelFrame(tab_tools, text="图层显示")
        layer_frame.pack(fill=tk.X, padx=6, pady=6)
        layer_btns = ttk.Frame(layer_frame)
        layer_btns.pack(fill=tk.X, padx=4, pady=4)
        for col, (mode, label) in enumerate(LAYER_MODES):
            btn = tk.Button(
                layer_btns, text=label, width=8, font=("Microsoft YaHei", 9),
                bg="#2a2a32", fg="white", relief=tk.RAISED,
                command=lambda m=mode: self._set_layer_mode(m),
            )
            btn.grid(row=0, column=col, padx=2, pady=2, sticky=tk.EW)
            self._layer_buttons[mode] = btn
        for c in range(3):
            layer_btns.columnconfigure(c, weight=1)
        self._sync_layer_buttons()

        ttk.Label(tab_tools, text="绘制工具", font=("Microsoft YaHei", 10, "bold")).pack(anchor=tk.W, padx=8, pady=(4, 2))
        self.tool_var = tk.StringVar(value="paint")
        tool_grid = ttk.Frame(tab_tools)
        tool_grid.pack(fill=tk.X, padx=6, pady=4)
        for idx, (tool_id, label, _key) in enumerate(TOOL_GRID):
            btn = tk.Button(
                tool_grid, text=label, width=7, font=("Microsoft YaHei", 9),
                bg="#2e2e36", fg="white", relief=tk.RAISED,
                command=lambda t=tool_id: self._select_tool(t),
            )
            btn.grid(row=idx // 2, column=idx % 2, padx=2, pady=2, sticky=tk.EW)
            self._tool_buttons[tool_id] = btn
        tool_grid.columnconfigure(0, weight=1)
        tool_grid.columnconfigure(1, weight=1)
        self._sync_tool_buttons()

        brush_frame = ttk.LabelFrame(tab_tools, text="笔刷大小 [ ]  ·  Alt+右键拖")
        brush_frame.pack(fill=tk.X, padx=6, pady=8)
        self.brush_lbl = ttk.Label(brush_frame, text=f"{self.brush_size} 格")
        self.brush_lbl.pack(anchor=tk.W, padx=8, pady=(4, 0))
        self.brush_scale = ttk.Scale(
            brush_frame, from_=1, to=20, orient=tk.HORIZONTAL,
            command=lambda _v: self._on_brush_size(),
        )
        self.brush_scale.set(self.brush_size)
        self.brush_scale.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(tab_tools, text="左键绘制 · 中键平移 · Alt+右键调笔刷", foreground="#888").pack(anchor=tk.W, padx=8, pady=8)

        ttk.Label(tab_brush, text="地板颜色").pack(anchor=tk.W, padx=8, pady=(6, 2))
        preset_frame = ttk.Frame(tab_brush)
        preset_frame.pack(fill=tk.X, padx=8)
        for idx, (_name, hex_c) in enumerate(COLOR_PRESETS):
            tk.Button(
                preset_frame, bg=hex_c, width=3, height=1, relief=tk.RIDGE,
                command=lambda c=hex_c: self._set_color(c),
            ).grid(row=idx // 3, column=idx % 3, padx=2, pady=2)
        color_row = ttk.Frame(tab_brush)
        color_row.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(color_row, text="当前地板色").pack(side=tk.LEFT)
        self.color_btn = tk.Button(color_row, bg=self.brush_color, width=5, command=self._pick_color)
        self.color_btn.pack(side=tk.RIGHT)

        ttk.Label(tab_brush, text="障碍颜色/材质").pack(anchor=tk.W, padx=8, pady=(8, 2))
        obs_row = ttk.Frame(tab_brush)
        obs_row.pack(fill=tk.X, padx=8, pady=2)
        ttk.Label(obs_row, text="当前障碍色").pack(side=tk.LEFT)
        self.obstacle_btn = tk.Button(obs_row, bg=self.obstacle_color, width=5, command=self._pick_obstacle_color)
        self.obstacle_btn.pack(side=tk.RIGHT)
        obs_preset_frame = ttk.Frame(tab_brush)
        obs_preset_frame.pack(fill=tk.X, padx=8, pady=4)
        for idx, (_name, hex_c) in enumerate(OBSTACLE_PRESETS):
            tk.Button(
                obs_preset_frame, bg=hex_c, width=3, height=1, relief=tk.RIDGE,
                command=lambda c=hex_c: self._set_obstacle_color(c),
            ).grid(row=idx // 3, column=idx % 3, padx=2, pady=2)

        box_frame = ttk.LabelFrame(tab_brush, text="箱子预设 (阻挡冲击波)")
        box_frame.pack(fill=tk.X, padx=6, pady=8)
        for idx, (label, bw, bh) in enumerate(BOX_PRESETS):
            ttk.Button(
                box_frame, text=label,
                command=lambda w=bw, h=bh, n=label: self._select_box_preset(w, h, n),
            ).grid(row=idx // 2, column=idx % 2, padx=2, pady=2, sticky=tk.EW)
        self.box_preset_lbl = ttk.Label(box_frame, text="当前: 箱 3×3", foreground="#888")
        self.box_preset_lbl.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=4, pady=4)

        cs2_frame = ttk.LabelFrame(tab_objects, text="CS2 快捷标记")
        cs2_frame.pack(fill=tk.X, padx=6, pady=6)
        for idx, (label, color, kind) in enumerate(CS2_MARKERS):
            ttk.Button(
                cs2_frame, text=label,
                command=lambda l=label, c=color, k=kind: self._place_cs2_marker(l, c, k),
            ).grid(row=idx // 2, column=idx % 2, padx=2, pady=2, sticky=tk.EW)

        ref_frame = ttk.LabelFrame(tab_objects, text="参考图")
        ref_frame.pack(fill=tk.X, padx=6, pady=6)
        self.ref_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ref_frame, text="显示参考图", variable=self.ref_var, command=self._toggle_reference).pack(anchor=tk.W, padx=8, pady=2)
        ttk.Label(ref_frame, text="透明度").pack(anchor=tk.W, padx=8)
        self.ref_scale = ttk.Scale(ref_frame, from_=0.1, to=0.9, orient=tk.HORIZONTAL, command=lambda _v: self._on_ref_opacity())
        self.ref_scale.set(self.ref_opacity)
        self.ref_scale.pack(fill=tk.X, padx=8, pady=4)

        list_frame = ttk.LabelFrame(tab_objects, text="爆炸源 / 标记点")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        ttk.Label(list_frame, text="爆炸源").pack(anchor=tk.W, padx=4)
        self.source_list = tk.Listbox(list_frame, height=2, exportselection=False)
        self.source_list.pack(fill=tk.X, padx=4, pady=2)
        self.source_list.bind("<<ListboxSelect>>", self._on_source_select)
        ttk.Label(list_frame, text="标记点").pack(anchor=tk.W, padx=4, pady=(4, 0))
        self.marker_list = tk.Listbox(list_frame, height=3, exportselection=False)
        self.marker_list.pack(fill=tk.X, padx=4, pady=2)

    def _build_canvas_area(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, padx=8, pady=4)
        self.map_title = ttk.Label(header, text="", font=("Microsoft YaHei", 13, "bold"))
        self.map_title.pack(side=tk.LEFT)
        ttk.Button(header, text="撤销", command=self._undo_action).pack(side=tk.RIGHT, padx=4)
        ttk.Button(header, text="重做", command=self._redo_action).pack(side=tk.RIGHT, padx=4)
        ttk.Button(header, text="重置视图", command=self._reset_view).pack(side=tk.RIGHT, padx=4)
        for mode, label in LAYER_MODES:
            btn = tk.Button(
                header, text=label, width=7, font=("Microsoft YaHei", 9),
                bg="#2a2a32", fg="white", relief=tk.RAISED,
                command=lambda m=mode: self._set_layer_mode(m),
            )
            btn.pack(side=tk.RIGHT, padx=2)
            self._header_layer_buttons[mode] = btn
        self._sync_layer_buttons()

        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.canvas = tk.Canvas(canvas_frame, bg="#08080a", highlightthickness=1, highlightbackground="#444", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Configure>", lambda _e: self._schedule_refresh())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<ButtonPress-2>", self._on_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonRelease-2>", self._on_pan_end)
        self.canvas.bind("<ButtonPress-3>", self._on_right_click)
        self.canvas.bind("<Alt-ButtonPress-3>", self._on_brush_resize_start)
        self.canvas.bind("<Alt-B3-Motion>", self._on_brush_resize_drag)
        self.canvas.bind("<Alt-ButtonRelease-3>", self._on_brush_resize_end)
        self.canvas.bind("<Motion>", self._on_mouse_motion)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Control-MouseWheel>", self._on_wheel)
        self.canvas.bind("<Leave>", lambda _e: self.canvas.delete("brush_preview"))
        self.canvas.bind("<Enter>", lambda _e: self.canvas.focus_set())

    def _build_status_bar(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_var = tk.StringVar(value="就绪 · 可从雷达图一键导入 Mirage")
        ttk.Label(bar, textvariable=self.status_var, anchor=tk.W).pack(fill=tk.X, padx=8, pady=3)

    def _bind_keys(self) -> None:
        key_map = {
            "b": "paint", "o": "obstacle", "e": "eraser", "f": "flood",
            "l": "line", "r": "rect", "i": "eyedropper", "c": "explosion",
            "m": "text", "v": "move", "p": "box", "g": lambda: self._toggle_grid(),
            "1": lambda: self._set_layer_mode("all"),
            "2": lambda: self._set_layer_mode("floor"),
            "3": lambda: self._set_layer_mode("obstacle"),
        }
        for key, action in key_map.items():
            if callable(action):
                self.bind(f"<{key}>", lambda _e, fn=action: fn())
                self.bind(f"<{key.upper()}>", lambda _e, fn=action: fn())
            else:
                self.bind(f"<{key}>", lambda _e, t=action: self._select_tool(t))
                self.bind(f"<{key.upper()}>", lambda _e, t=action: self._select_tool(t))
        self.bind("<Control-z>", lambda _e: self._undo_action())
        self.bind("<Control-y>", lambda _e: self._redo_action())
        self.bind("<bracketleft>", lambda _e: self._adjust_brush(-1))
        self.bind("<bracketright>", lambda _e: self._adjust_brush(1))
        self.bind("<Control-s>", lambda _e: self._save_map())
        self.bind("<plus>", lambda _e: self._zoom_by(1.15))
        self.bind("<minus>", lambda _e: self._zoom_by(1 / 1.15))
        self.bind("<Key-0>", lambda _e: self._reset_view())
        for key in ("Alt_L", "Alt_R"):
            self.bind(f"<KeyPress-{key}>", self._on_alt_down)
            self.bind(f"<KeyRelease-{key}>", self._on_alt_up)
        self.canvas.bind("<KeyPress-Alt_L>", self._on_alt_down)
        self.canvas.bind("<KeyPress-Alt_R>", self._on_alt_down)
        self.canvas.bind("<KeyRelease-Alt_L>", self._on_alt_up)
        self.canvas.bind("<KeyRelease-Alt_R>", self._on_alt_up)

    # --- Undo / view ----------------------------------------------------------

    def _push_undo(self) -> None:
        self._undo.append(snapshot(self.bundle))
        if len(self._undo) > 60:
            self._undo.pop(0)
        self._redo.clear()

    def _undo_action(self) -> None:
        if len(self._undo) <= 1:
            return
        self._redo.append(self._undo.pop())
        restore(self.bundle, self._undo[-1])
        self._refresh_lists()
        self._refresh_canvas()
        self.status_var.set("已撤销")

    def _redo_action(self) -> None:
        if not self._redo:
            return
        snap = self._redo.pop()
        self._undo.append(snap)
        restore(self.bundle, snap)
        self._refresh_lists()
        self._refresh_canvas()
        self.status_var.set("已重做")

    def _zoom_by(self, factor: float) -> None:
        self.zoom = float(np.clip(self.zoom * factor, 0.5, 8.0))
        self._refresh_canvas()
        self.status_var.set(f"缩放 {self.zoom:.1f}x")

    def _reset_view(self) -> None:
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._refresh_canvas()

    def _on_wheel(self, event) -> None:
        delta = 1.12 if event.delta > 0 else 1 / 1.12
        self._zoom_by(delta)

    def _on_pan_start(self, event) -> None:
        self._panning = True
        self._pan_anchor = (event.x - self.pan_x, event.y - self.pan_y)

    def _on_pan_move(self, event) -> None:
        if self._panning:
            self.pan_x = event.x - self._pan_anchor[0]
            self.pan_y = event.y - self._pan_anchor[1]
            self._refresh_canvas()

    def _on_pan_end(self, _event) -> None:
        self._panning = False

    # --- Coordinates ----------------------------------------------------------

    def _canvas_size(self) -> tuple[int, int]:
        return max(int(self.canvas.winfo_width()), 400), max(int(self.canvas.winfo_height()), 300)

    def _map_layout(self) -> tuple[float, float, float, float]:
        """Return cell_w, cell_h, offset_x, offset_y on canvas."""
        cw, ch = self._canvas_size()
        gw, gh = self.bundle.grid_w, self.bundle.grid_h
        base_cell = min(cw / gw, ch / gh) * self.zoom
        map_w = gw * base_cell
        map_h = gh * base_cell
        ox = (cw - map_w) / 2 + self.pan_x
        oy = (ch - map_h) / 2 + self.pan_y
        return base_cell, base_cell, ox, oy

    def _event_to_grid(self, event) -> tuple[int, int, float, float]:
        cell_w, cell_h, ox, oy = self._map_layout()
        gw, gh = self.bundle.grid_w, self.bundle.grid_h
        px = event.x - ox
        py = event.y - oy
        i = int(np.clip(px / cell_w, 0, gw - 1))
        j = int(np.clip((gh - 1) - py / cell_h, 0, gh - 1))
        nx, ny = self.bundle.grid_to_norm(i, j)
        return i, j, nx, ny

    # --- Rendering ------------------------------------------------------------

    def _render_image(self) -> Image.Image:
        cw, ch = self._canvas_size()
        gw, gh = self.bundle.grid_w, self.bundle.grid_h
        cell_w, cell_h, ox, oy = self._map_layout()
        img = Image.new("RGB", (cw, ch), (8, 8, 10))
        draw = ImageDraw.Draw(img)

        if self.show_reference and self._reference_rgb is not None and self.layer_mode in ("all", "floor"):
            ref = Image.fromarray(self._reference_rgb).resize((int(gw * cell_w), int(gh * cell_h)), Image.Resampling.BILINEAR)
            ref.putalpha(int(255 * self.ref_opacity))
            img.paste(ref, (int(ox), int(oy)), ref)

        mode = self.layer_mode
        for j in range(gh):
            for i in range(gw):
                x0 = int(ox + i * cell_w)
                y0 = int(oy + (gh - 1 - j) * cell_h)
                x1 = int(ox + (i + 1) * cell_w)
                y1 = int(oy + (gh - j) * cell_h)
                rgb = tuple(int(v) for v in self.bundle.cell_colors[j, i])
                floor = is_floor_cell(self.bundle, j, i)
                obstacle = is_obstacle_cell(self.bundle, j, i)

                if mode == "floor":
                    if floor:
                        draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=rgb)
                    elif self.show_grid:
                        draw.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(22, 22, 28))
                elif mode == "obstacle":
                    if obstacle:
                        draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=rgb)
                        draw.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(200, 90, 50))
                    elif self.show_grid:
                        draw.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(28, 28, 34))
                else:
                    if floor:
                        draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=rgb)
                    elif obstacle:
                        draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=rgb)
                    elif self.show_grid:
                        draw.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(22, 22, 28))

        if self.show_grid and cell_w >= 4:
            for i in range(gw + 1):
                x = int(ox + i * cell_w)
                draw.line([(x, int(oy)), (x, int(oy + gh * cell_h))], fill=(40, 40, 50))
            for j in range(gh + 1):
                y = int(oy + j * cell_h)
                draw.line([(int(ox), y), (int(ox + gw * cell_w), y)], fill=(40, 40, 50))

        draw.rectangle(
            [int(ox), int(oy), int(ox + gw * cell_w), int(oy + gh * cell_h)],
            outline=(90, 90, 100), width=2,
        )
        return img

    def _draw_overlays(self) -> None:
        if not self.show_markers_layer:
            return
        self.canvas.delete("overlay")
        cell_w, cell_h, ox, oy = self._map_layout()
        gw, gh = self.bundle.grid_w, self.bundle.grid_h

        def to_px(nx: float, ny: float) -> tuple[float, float]:
            i = nx * (gw - 1)
            j = ny * (gh - 1)
            px = ox + i * cell_w + cell_w / 2
            py = oy + (gh - 1 - j) * cell_h + cell_h / 2
            return px, py

        for src in self.bundle.explosion_sources:
            px, py = to_px(*src.norm)
            sel = src.id == self._selected_source_id
            r = 9 if sel else 7
            self.canvas.create_oval(px - r, py - r, px + r, py + r, outline=src.color, width=3 if sel else 2, tags="overlay")
            self.canvas.create_text(px, py - 16, text=src.label, fill=src.color, font=("Microsoft YaHei", 9, "bold"), tags="overlay")

        for marker in self.bundle.markers:
            px, py = to_px(*marker.norm)
            self.canvas.create_oval(px - 6, py - 6, px + 6, py + 6, outline=marker.color, width=2, tags="overlay")
            if marker.label:
                self.canvas.create_text(px, py - 13, text=marker.label, fill=marker.color, font=("Microsoft YaHei", 8), tags="overlay")

    def _schedule_refresh(self) -> None:
        if not self._refresh_scheduled:
            self._refresh_scheduled = True
            self.after(16, self._do_refresh)

    def _do_refresh(self) -> None:
        self._refresh_scheduled = False
        self._refresh_canvas()

    def _refresh_canvas(self) -> None:
        img = self._render_image()
        self._photo = ImageTk.PhotoImage(img)
        self.canvas.delete("map")
        cw, ch = self._canvas_size()
        self.canvas.create_image(0, 0, image=self._photo, anchor=tk.NW, tags="map")
        self._draw_overlays()
        self._draw_brush_preview()
        layer_labels = dict(LAYER_MODES)
        self.map_title.config(
            text=f"{self.bundle.map_name}  ({self.bundle.grid_w}×{self.bundle.grid_h})  "
            f"{self.zoom:.1f}x  ·  {layer_labels.get(self.layer_mode, '')}",
        )

    def _refresh_lists(self) -> None:
        self.source_list.delete(0, tk.END)
        for src in self.bundle.explosion_sources:
            self.source_list.insert(tk.END, f"{src.label}  ({src.norm[0]:.2f}, {src.norm[1]:.2f})")
        self.marker_list.delete(0, tk.END)
        for m in self.bundle.markers:
            self.marker_list.insert(tk.END, f"{m.label or m.id}  ({m.norm[0]:.2f}, {m.norm[1]:.2f})")

    # --- Drawing --------------------------------------------------------------

    def _select_tool(self, tool_id: str) -> None:
        self.tool_var.set(tool_id)
        self._sync_tool_buttons()
        self._on_tool_change()

    def _on_tool_change(self) -> None:
        hints = {t[0]: t[2] for t in TOOLS}
        self.status_var.set(hints.get(self.tool_var.get(), ""))

    def _on_brush_size(self) -> None:
        self.brush_size = max(1, int(float(self.brush_scale.get())))
        self.brush_lbl.config(text=f"{self.brush_size} 格")
        self._draw_brush_preview()

    def _adjust_brush(self, delta: int) -> None:
        self.brush_size = int(np.clip(self.brush_size + delta, 1, 20))
        self.brush_scale.set(self.brush_size)
        self.brush_lbl.config(text=f"{self.brush_size} 格")
        self._draw_brush_preview()

    def _set_color(self, hex_color: str) -> None:
        self.brush_color = hex_color
        self._brush_rgb = tuple(int(hex_color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        self.color_btn.config(bg=hex_color)

    def _set_obstacle_color(self, hex_color: str) -> None:
        self.obstacle_color = hex_color
        self._obstacle_rgb = tuple(int(hex_color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        self.obstacle_btn.config(bg=hex_color)

    def _pick_color(self) -> None:
        rgb, hex_color = colorchooser.askcolor(color=self.brush_color, title="地板颜色")
        if hex_color:
            self._set_color(hex_color)

    def _pick_obstacle_color(self) -> None:
        rgb, hex_color = colorchooser.askcolor(color=self.obstacle_color, title="障碍物颜色")
        if hex_color:
            self._set_obstacle_color(hex_color)

    def _select_box_preset(self, w: int, h: int, label: str) -> None:
        self._box_w, self._box_h = w, h
        self._select_tool("box")
        self.box_preset_lbl.config(text=f"当前: {label}")
        self.status_var.set(f"箱子预设 {label} — 点击地图放置")

    def _is_alt_down(self, event=None) -> bool:
        if event is not None and bool(event.state & 0x20000):
            return True
        return self._alt_key_held

    def _on_alt_down(self, _event=None) -> None:
        self._alt_key_held = True

    def _on_alt_up(self, _event=None) -> None:
        self._alt_key_held = False

    def _on_mouse_motion(self, event) -> None:
        self._mouse_xy = (event.x, event.y)
        self._draw_brush_preview(event)

    def _brush_is_square(self) -> bool:
        return self.tool_var.get() in ("obstacle", "box", "rect")

    def _grid_center_px(self, i: int, j: int) -> tuple[float, float]:
        cell_w, cell_h, ox, oy = self._map_layout()
        gh = self.bundle.grid_h
        px = ox + i * cell_w + cell_w / 2
        py = oy + (gh - 1 - j) * cell_h + cell_h / 2
        return px, py

    def _draw_brush_preview(self, event=None) -> None:
        if not hasattr(self, "canvas"):
            return
        self.canvas.delete("brush_preview")
        tool = self.tool_var.get()
        if tool not in ("paint", "obstacle", "eraser", "box"):
            return
        x = event.x if event else self._mouse_xy[0]
        y = event.y if event else self._mouse_xy[1]

        class E:
            pass
        ev = E()
        ev.x, ev.y = x, y
        i, j, _, _ = self._event_to_grid(ev)
        cx, cy = self._grid_center_px(i, j)
        cell_w, cell_h, _, _ = self._map_layout()

        if tool == "box":
            bw, bh = self._box_w, self._box_h
            w_px = bw * cell_w
            h_px = bh * cell_h
            color = self.obstacle_color
            self.canvas.create_rectangle(
                cx - w_px / 2, cy - h_px / 2, cx + w_px / 2, cy + h_px / 2,
                outline=color, width=2, dash=(4, 3), tags="brush_preview",
            )
            return

        size = self.brush_size
        color = self.obstacle_color if tool == "obstacle" else (self.brush_color if tool == "paint" else "#888888")
        if self._brush_is_square():
            w_px = size * cell_w
            h_px = size * cell_h
            self.canvas.create_rectangle(
                cx - w_px / 2, cy - h_px / 2, cx + w_px / 2, cy + h_px / 2,
                outline=color, width=2, tags="brush_preview",
            )
        else:
            r_px = max(cell_w, cell_h) * size / 2
            self.canvas.create_oval(
                cx - r_px, cy - r_px, cx + r_px, cy + r_px,
                outline=color, width=2, tags="brush_preview",
            )

    def _on_brush_resize_start(self, event) -> None:
        self._brush_resize_active = True
        self._brush_resize_origin_x = event.x
        self._brush_resize_origin_size = self.brush_size

    def _on_brush_resize_drag(self, event) -> None:
        if not self._brush_resize_active:
            return
        delta = event.x - self._brush_resize_origin_x
        new_size = int(np.clip(self._brush_resize_origin_size + round(delta / 10), 1, 20))
        if new_size != self.brush_size:
            self.brush_size = new_size
            self.brush_scale.set(new_size)
            self.brush_lbl.config(text=f"{self.brush_size} 格")
            self.status_var.set(f"笔刷大小 {self.brush_size} 格")
            self._draw_brush_preview(event)

    def _on_brush_resize_end(self, _event) -> None:
        self._brush_resize_active = False

    def _try_pick_color(self, event, i: int, j: int) -> bool:
        if not self._is_alt_down(event):
            return False
        rgb = pick_cell_color(self.bundle, i, j)
        hex_c = "#%02x%02x%02x" % rgb
        tool = self.tool_var.get()
        if tool in ("obstacle", "box"):
            self._set_obstacle_color(hex_c)
        else:
            self._set_color(hex_c)
        self.status_var.set(f"吸附颜色 {hex_c}")
        self._draw_brush_preview(event)
        return True

    def _stamp_at(self, i: int, j: int) -> None:
        tool = self.tool_var.get()
        square = self._brush_is_square()
        if tool == "paint":
            stamp_brush(self.bundle, i, j, self.brush_size, walkable=True, rgb=self._brush_rgb, square=False)
        elif tool == "obstacle":
            stamp_brush(self.bundle, i, j, self.brush_size, walkable=False, rgb=self._obstacle_rgb, square=True)
        elif tool == "eraser":
            stamp_brush(self.bundle, i, j, self.brush_size, walkable=True, rgb=DEFAULT_FLOOR_RGB, square=False)
        elif tool == "flood":
            fill_region(self.bundle, i, j, walkable=True, rgb=self._brush_rgb)
        elif tool == "eyedropper":
            self._set_color("#%02x%02x%02x" % pick_cell_color(self.bundle, i, j))
        elif tool == "box":
            stamp_box(
                self.bundle, i, j, self._box_w, self._box_h,
                walkable=False, rgb=self._obstacle_rgb,
            )

    def _on_press(self, event) -> None:
        if self._panning:
            return
        tool = self.tool_var.get()
        i, j, nx, ny = self._event_to_grid(event)

        if tool == "move":
            self._move_target = nearest_marker(self.bundle, nx, ny)
            self._dragging = bool(self._move_target)
            return

        if tool in ("line", "rect"):
            if self._try_pick_color(event, i, j):
                return
            self._push_undo()
            self._stroke_start = (i, j)
            self._dragging = True
            return

        if tool == "explosion":
            self._push_undo()
            self._place_explosion(nx, ny, ask=False)
            return

        if tool == "text":
            self._push_undo()
            self._place_marker(nx, ny)
            return

        if tool == "box":
            self._push_undo()
            self._stamp_at(i, j)
            self._schedule_refresh()
            self.status_var.set(f"已放置箱子 {self._box_w}×{self._box_h}")
            return

        if self._try_pick_color(event, i, j):
            return

        self._push_undo()
        self._dragging = True
        self._last_ij = (i, j)
        self._stamp_at(i, j)
        self._schedule_refresh()
        self.status_var.set(f"({i},{j}) norm=({nx:.3f},{ny:.3f})")

    def _on_drag(self, event) -> None:
        if not self._dragging or self._panning:
            return
        tool = self.tool_var.get()
        i, j, nx, ny = self._event_to_grid(event)

        if tool == "move" and self._move_target is not None:
            self._move_target.norm = (nx, ny)
            self._schedule_refresh()
            return

        if tool in ("line", "rect") and self._stroke_start:
            restore(self.bundle, self._undo[-1])
            i0, j0 = self._stroke_start
            use_obstacle = self.tool_var.get() == "obstacle"
            rgb = self._obstacle_rgb if use_obstacle else self._brush_rgb
            if tool == "line":
                stamp_line(
                    self.bundle, i0, j0, i, j, self.brush_size,
                    walkable=not use_obstacle, rgb=rgb, square=use_obstacle,
                )
            else:
                fill_rect(self.bundle, i0, j0, i, j, walkable=not use_obstacle, rgb=rgb)
            self._schedule_refresh()
            return

        if self._try_pick_color(event, i, j):
            return

        if tool in ("paint", "obstacle", "eraser") and self._last_ij:
            i0, j0 = self._last_ij
            if tool == "paint":
                stamp_line(self.bundle, i0, j0, i, j, self.brush_size, walkable=True, rgb=self._brush_rgb, square=False)
            elif tool == "obstacle":
                stamp_line(self.bundle, i0, j0, i, j, self.brush_size, walkable=False, rgb=self._obstacle_rgb, square=True)
            else:
                stamp_line(self.bundle, i0, j0, i, j, self.brush_size, walkable=True, rgb=DEFAULT_FLOOR_RGB, square=False)
            self._last_ij = (i, j)
            self._schedule_refresh()

    def _on_release(self, event) -> None:
        if self._stroke_start and self.tool_var.get() in ("line", "rect"):
            self._refresh_lists()
        self._dragging = False
        self._stroke_start = None
        self._last_ij = None
        self._move_target = None

    def _place_explosion(self, nx: float, ny: float, ask: bool = True) -> None:
        label = "C4"
        if ask:
            val = simpledialog.askstring("爆炸源", "标签:", initialvalue="C4", parent=self)
            if val is None:
                return
            label = val
        src_id = f"bomb_{len(self.bundle.explosion_sources) + 1}"
        src = ExplosionSource(id=src_id, norm=(nx, ny), label=label, color="#ff6600")
        self.bundle.explosion_sources.append(src)
        self._selected_source_id = src_id
        self._refresh_lists()
        self._refresh_canvas()

    def _place_marker(self, nx: float, ny: float, label: str | None = None, color: str = "#66ccff") -> None:
        if label is None:
            label = simpledialog.askstring("标记", "文字:", initialvalue="标记", parent=self) or ""
        if not label:
            return
        mk_id = f"marker_{len(self.bundle.markers) + 1}"
        self.bundle.markers.append(MapMarker(id=mk_id, norm=(nx, ny), label=label, color=color))
        self._refresh_lists()
        self._refresh_canvas()

    def _place_cs2_marker(self, label: str, color: str, kind: str) -> None:
        self.status_var.set(f"点击地图放置: {label}")

        def once(event):
            self.canvas.unbind("<ButtonPress-1>")
            self.canvas.bind("<ButtonPress-1>", self._on_press)
            _, _, nx, ny = self._event_to_grid(event)
            self._push_undo()
            if kind == "bomb":
                src = ExplosionSource(
                    id=f"bomb_{label}", norm=(nx, ny),
                    label="C4" if "A" in label else label, color=color,
                )
                self.bundle.explosion_sources.append(src)
                self._selected_source_id = src.id
            else:
                self.bundle.markers.append(MapMarker(id=label, norm=(nx, ny), label=label, color=color))
            self._refresh_lists()
            self._refresh_canvas()
            self.status_var.set(f"已放置 {label}")

        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.bind("<ButtonPress-1>", once)

    def _on_right_click(self, event) -> None:
        if self._is_alt_down(event):
            return
        _, _, nx, ny = self._event_to_grid(event)
        target = nearest_marker(self.bundle, nx, ny, threshold=0.05)
        if target is None:
            return
        self._push_undo()
        if isinstance(target, ExplosionSource):
            self.bundle.explosion_sources.remove(target)
        else:
            self.bundle.markers.remove(target)
        self._refresh_lists()
        self._refresh_canvas()
        self.status_var.set("已删除标记")

    def _on_source_select(self, _event=None) -> None:
        sel = self.source_list.curselection()
        if sel and sel[0] < len(self.bundle.explosion_sources):
            self._selected_source_id = self.bundle.explosion_sources[sel[0]].id
            self._draw_overlays()

    # --- Reference / import ---------------------------------------------------

    def _toggle_reference(self) -> None:
        self.show_reference = self.ref_var.get()
        self._refresh_canvas()

    def _on_ref_opacity(self) -> None:
        self.ref_opacity = float(self.ref_scale.get())
        if self.show_reference:
            self._refresh_canvas()

    def _set_reference(self, rgb: np.ndarray, path: Path | None = None) -> None:
        self._reference_rgb = rgb
        self._reference_path = path
        self.ref_var.set(True)
        self.show_reference = True
        self._refresh_canvas()

    def _import_radar_image(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 CS2 雷达图",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.bmp"), ("所有", "*.*")],
            initialdir=str(mirage_radar_path().parent) if mirage_radar_path().parent.exists() else None,
        )
        if not path:
            return
        if not messagebox.askyesno("导入", "从雷达图自动生成可走区/颜色/站点？\n（将覆盖当前地图）"):
            return
        try:
            name = Path(path).stem
            bundle, rgb = import_from_radar_image(
                Path(path), map_name=name, cs2_mirage=("mirage" in path.lower()),
            )
            self.bundle = bundle
            self.bundle_path = None
            self._set_reference(rgb, Path(path))
            self._selected_source_id = bundle.explosion_sources[0].id if bundle.explosion_sources else None
            self._undo.clear()
            self._redo.clear()
            self._push_undo()
            self._refresh_lists()
            self._refresh_canvas()
            self.status_var.set(f"已从雷达图导入 · 可走格 {bundle.walkable.sum()}")
            messagebox.showinfo("导入完成", f"可走区域: {bundle.walkable.sum()} 格\n爆炸源: {len(bundle.explosion_sources)}\n标记: {len(bundle.markers)}")
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc))

    def _import_mirage_radar(self) -> None:
        if not messagebox.askyesno("Mirage", "一键从 de_mirage 雷达图生成完整地图？"):
            return
        try:
            self.bundle = import_mirage_radar("de_mirage")
            self.bundle_path = None
            from yty_manim.tools.map_editor.map_radar_import import load_rgb
            self._set_reference(load_rgb(mirage_radar_path()), mirage_radar_path())
            self._selected_source_id = self.bundle.explosion_sources[0].id if self.bundle.explosion_sources else None
            self._undo.clear()
            self._redo.clear()
            self._push_undo()
            self._refresh_lists()
            self._refresh_canvas()
            self.status_var.set(f"Mirage 导入完成 · {self.bundle.walkable.sum()} 可走格")
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc))

    # --- File ops -------------------------------------------------------------

    def _new_map(self) -> None:
        if not self._confirm_discard():
            return
        name = simpledialog.askstring("新建", "地图名:", initialvalue="untitled", parent=self)
        if not name:
            return
        self.bundle = MapBundle.blank(name.strip())
        self.bundle_path = None
        self._reference_rgb = None
        self._undo.clear()
        self._redo.clear()
        self._push_undo()
        self._refresh_lists()
        self._refresh_canvas()

    def _open_map(self) -> None:
        if not self._confirm_discard():
            return
        path = filedialog.askdirectory(title="打开地图", initialdir=default_maps_dir())
        if not path:
            return
        try:
            self.bundle = MapBundle.load(Path(path))
            self.bundle_path = Path(path)
            ref = self.bundle_path / "reference.png"
            if ref.exists():
                from yty_manim.tools.map_editor.map_radar_import import load_rgb
                self._set_reference(load_rgb(ref), ref)
            self._selected_source_id = self.bundle.explosion_sources[0].id if self.bundle.explosion_sources else None
            self._undo.clear()
            self._redo.clear()
            self._push_undo()
            self._refresh_lists()
            self._refresh_canvas()
            self.status_var.set(f"已打开 {self.bundle.map_name}")
        except Exception as exc:
            messagebox.showerror("打开失败", str(exc))

    def _save_map(self) -> None:
        if self.bundle_path is None:
            self._save_as()
            return
        try:
            self.bundle.save(self.bundle_path)
            self.status_var.set(f"已保存 {self.bundle_path}")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def _save_as(self) -> None:
        name = simpledialog.askstring("另存为", "地图名:", initialvalue=self.bundle.map_name, parent=self)
        if not name:
            return
        self.bundle.map_name = name.strip()
        path = default_maps_dir() / self.bundle.map_name
        try:
            self.bundle.save(path)
            self.bundle_path = path
            self.status_var.set(f"已导出 {path}")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def _preview_manim(self) -> None:
        if self.bundle_path is None:
            if messagebox.askyesno("保存", "预览前需保存，现在保存？"):
                self._save_as()
            if self.bundle_path is None:
                return
        env = os.environ.copy()
        env["MAP_BUNDLE"] = str(self.bundle_path)
        root = Path(__file__).resolve().parents[3]
        try:
            subprocess.Popen(
                [sys.executable, "-m", "manim", "-ql", "yty_manim/application/map_shockwave_scene.py", "CustomMapShockwaveScene"],
                cwd=root, env=env,
            )
            self.status_var.set("Manim 预览已启动")
        except Exception as exc:
            messagebox.showerror("预览失败", str(exc))

    def _confirm_discard(self) -> bool:
        return messagebox.askyesno("确认", "放弃未保存更改？") if self.bundle_path else True

    def _on_close(self) -> None:
        self.destroy()
