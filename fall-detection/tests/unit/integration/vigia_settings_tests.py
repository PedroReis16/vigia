import json
from uuid import uuid4

import pytest

from app.integration.models.vigia_settings import VigiaSettings


def test_from_dict_given_command_with_object_id_should_parse_command_name() -> None:
    device_id = str(uuid4())
    data = {
        "device_id": device_id,
        "commands": [{"object_id": "stream"}],
        "attributes": [{"name": "capture", "type": "Boolean", "object_id": "ca"}],
    }

    settings = VigiaSettings._from_dict(data)

    assert settings.commands[0].name == "stream"


def test_from_dict_given_attribute_with_missing_name_should_raise_value_error() -> None:
    data = {"attributes": [{"type": "Text"}]}

    with pytest.raises(ValueError, match="Invalid attribute name"):
        VigiaSettings._from_dict(data)


def test_to_json_given_valid_settings_should_include_serialized_device_id() -> None:
    settings = VigiaSettings(device_id=uuid4())
    payload = json.loads(settings.to_json())

    assert isinstance(payload["device_id"], str)
