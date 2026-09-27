import time

import logging

logger = logging.getLogger(__name__)

def run_integration() -> None:
    """
    Processo principal de integração do dispositivo com o FIWARE,
    recebendo notificações do MQQT e publicando informações para o broker a partir da classificação
    """
    logger.info("Integration running")
    
    try:
        while True:
            logger.info("Integração")
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Integration stopped")
    except Exception as e:
        logger.error(f"Integration error: {e}")
        raise e