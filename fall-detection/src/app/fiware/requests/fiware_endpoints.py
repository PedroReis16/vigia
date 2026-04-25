from __future__ import annotations

import os


def fiware_root_url() -> str:
    return (os.getenv("FIWARE_PATH") or "").rstrip("/")


def iot_agent_url() -> str:
    return f"{fiware_root_url()}/iot-agent"


def orion_url() -> str:
    return f"{fiware_root_url()}/orion"


def sth_comet_url() -> str:
    return f"{fiware_root_url()}/sth-comet"
