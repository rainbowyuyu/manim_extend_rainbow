# HLAE 加固版 v2.6e-R 使用说明

基于 Purp1e `hlae.cfg` 加固。备份：`hlae_v2.6e_purp1e.bak.cfg`

## 加载

HLAE 启动 CS2 后：

```
exec hlae
```

默认进入 **LIVE 测试地图模式**（无需 `.dem`）。

看回放前请执行：

```
demomode
```

---

## 核心能力

### 1. 一键摄像机（无需回放）

| 按键 / 指令 | 作用 |
|-------------|------|
| **F3** / `live_cam` | 测试地图一键：隐 HUD + 开 campath + 进入 freecam |
| **F1** / `cam` | 通用一键 freecam（Demo / Live 都可用） |

运镜中：**WASD** 飞、**CapsLock** 加机位、**ESC** 退出运镜、`play_cam` 播放路径。

### 2. 暂停时仍能流畅运镜

| 按键 / 指令 | 作用 |
|-------------|------|
| **F2** / **鼠标中键** / `p_cam` | 暂停局面后进入 **全速** freecam（不会卡顿） |
| `cam_fast` | 运镜加速（大范围摆机位） |
| `cam_precise` | 运镜精调（微调角度） |
| `freeze_hard` | 硬冻结粒子到 x0.001（移机位前请再按 F2） |
| 小键盘 **Enter** | 暂停运镜下添加机位 |
| `play_cam` | 退出 freecam → 解冻 → 播放路径 |

**为何流畅：** Live 暂停不再用 `host_timescale 0.001`（那会拖慢 freecam），改为 `bot_stop` + 相机 `timescale=1` + 提高 `ksens/msens`。Demo 仍用 `demo_pause`，相机独立全速。

操作时关闭控制台，用 **WASD** 飞镜头。

### 3. 丝滑子弹时刻

| 按键 / 指令 | 作用 |
|-------------|------|
| **M** | 档位循环：5%→10%→15%→25%→50%→100% |
| **-** / **/** | 减速 / 加速一档 |
| **F4** / `bt_reset` | 恢复 x1 |
| `bullet` | 直接 25% 子弹 |
| `ultraslow` | 直接 10% |

同时写入 `demo_timescale` 与 `host_timescale`，回放与测试地图通用。

---

## 推荐流程

### 测试地图（C4 / 爆炸）

```
map de_mirage
exec hlae
exec record_explosion_cinematic   // 可选：电影感爆炸 cfg
give weapon_c4
live_cam                          // 或按 F3
```

下包前 `bullet`（25%）→ 爆炸后慢镜飞镜头 → Caps 打机位 → Esc → `play_cam`

### Demo 回放运镜

```
exec hlae
demomode
playdemo your.dem
```

到关键时刻 → **F2** 暂停运镜 → 飞好机位 Caps 添加 → 小键盘+ 跳时间继续打点 → Esc → `play_cam`

---

## 模式切换

```
livemode   // 测试地图（默认）
demomode   // 回放 .dem
help_cam   // 打印快捷提示
```
