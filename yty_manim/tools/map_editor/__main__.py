"""Launch the windowed Manim map editor."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from yty_manim.tools.map_editor.editor_app import MapEditorApp
from yty_manim.tools.map_editor.map_bundle import MapBundle


def main() -> None:
    bundle: MapBundle | None = None
    bundle_path: Path | None = None

    if len(sys.argv) > 1:
        bundle_path = Path(sys.argv[1])
    elif os.environ.get("MAP_BUNDLE"):
        bundle_path = Path(os.environ["MAP_BUNDLE"])

    if bundle_path and bundle_path.is_dir():
        bundle = MapBundle.load(bundle_path)

    app = MapEditorApp(bundle)
    if bundle_path:
        app.bundle_path = bundle_path
        ref = bundle_path / "reference.png"
        if ref.exists():
            from yty_manim.tools.map_editor.map_radar_import import load_rgb
            app._set_reference(load_rgb(ref), ref)
    app.mainloop()


if __name__ == "__main__":
    main()
