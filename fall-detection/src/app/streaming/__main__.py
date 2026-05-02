from __future__ import annotations

from app.config import Settings
from app.path_setup import ensure_src_on_path
from app.streaming.runner import run_streaming

ensure_src_on_path()

def main() -> None:
    run_streaming(Settings.from_env())

if __name__ == "__main__":
    main()