"""
Exceções customizadas do sistema
"""


class EntityValidationException(Exception):
    """
    Exceção para erros operacionais relacionados a entidades do sistema
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
