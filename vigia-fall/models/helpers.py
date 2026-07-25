def helpers_convert_to_bool(value:str) -> bool:
    """
    Converte uma string para um booleano
    """
    v=value.strip().lower()
    return v in ("1", "true", "t", "yes", "y")