# import uvicorn

from src.core import get_settings
from src.runtime import LocalRuntime


def run() -> None:
    settings = get_settings()

    runtime = LocalRuntime(settings)
    runtime.run()
