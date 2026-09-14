"""Fixtures compartilhadas para os testes do vigia-fall."""

import pytest

from capture.frame_worker import get_worker
from shared import get_device_identity, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    get_device_identity.cache_clear()
    get_worker.cache_clear()
    yield
    get_settings.cache_clear()
    get_device_identity.cache_clear()
    get_worker.cache_clear()
