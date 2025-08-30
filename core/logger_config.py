import logging
import sys
from datetime import datetime

def setup_logger():
    """Configura o sistema de logging da aplicação"""
    
    # Configuração do formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Handler para arquivo
    file_handler = logging.FileHandler('chess_api.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Configuração do logger principal
    logger = logging.getLogger('chess_api')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Instância global do logger
logger = setup_logger()
