import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(log_file='app.log', log_level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(log_level)
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = RotatingFileHandler(
        filename=os.path.join(os.path.dirname(__file__), log_file),
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(log_level)
    logger.handlers.clear()
    logger.addHandler(file_handler)

setup_logging()