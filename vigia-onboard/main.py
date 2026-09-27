"""
Serviço para captura de imagens através de uma camera
"""

import logging
from src import run_capture

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    run_capture()
