#!/usr/bin/env python3
"""Desktop launcher: hologram by default. --classic opts into the original Tk UI."""

import os
import runpy
import sys
from pathlib import Path

project = Path(__file__).resolve().parent
if "--classic" in sys.argv[1:]:
    sys.argv.remove("--classic")
    old = project / "content" / "drive" / "MyDrive" / "Jarvis"
    if not (old / "jarvis_interface.py").is_file():
        raise SystemExit(
            "Classic UI not found. Extract this update into the original Jarvis-AI repository."
        )
    sys.path[:0] = [str(old), str(project / "python_deps")]
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.chdir(old)
    runpy.run_path(str(old / "jarvis_interface.py"), run_name="__main__")
else:
    sys.path.insert(0, str(project.parent))
    from launch_hologram import main

    raise SystemExit(main())
