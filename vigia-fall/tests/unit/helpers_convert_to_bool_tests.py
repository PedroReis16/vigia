"""Testes unitários para models.helpers.helpers_convert_to_bool."""

import pytest

from models.helpers import helpers_convert_to_bool


def test_helpers_convert_to_bool_ComValorTrue_RetornaVerdadeiro() -> None:
    # Arrange
    valor = "true"

    # Act
    resultado = helpers_convert_to_bool(valor)

    # Assert
    assert resultado is True


def test_helpers_convert_to_bool_ComValorFalse_RetornaFalso() -> None:
    # Arrange
    valor = "false"

    # Act
    resultado = helpers_convert_to_bool(valor)

    # Assert
    assert resultado is False


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("1", True),
        ("t", True),
        ("yes", True),
        ("y", True),
        (" TRUE ", True),
        ("0", False),
        ("no", False),
        ("", False),
    ],
)
def test_helpers_convert_to_bool_ComEntradasVariadas_RetornaEsperado(
    valor: str,
    esperado: bool,
) -> None:
    # Arrange — valor parametrizado

    # Act
    resultado = helpers_convert_to_bool(valor)

    # Assert
    assert resultado is esperado
