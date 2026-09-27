"""Contrato de import do pacote shared no Python do host."""

from __future__ import annotations

import shared
from shared.paths import capture_root, core_root, integration_root, onboard_root


def test_shared_GetSettings_EhLazy():
    """O host não pode carregar dotenv ao importar `shared` / `shared.paths`."""
    assert callable(getattr(shared, "__getattr__", None))


def test_integration_root_FicaSobOnboard():
    root = integration_root()
    assert root.name == "integration"
    assert root.parent == onboard_root()
    assert capture_root().parent == onboard_root()
    assert core_root().parent == onboard_root()
    assert core_root().name == "core"
