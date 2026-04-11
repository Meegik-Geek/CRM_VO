import logging
import os
from datetime import datetime

# Налаштування папки для логів
LOG_DIR = os.path.join(os.path.expanduser("~"), ".vstup2026", "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, f"vstup_{datetime.now().strftime('%Y-%m')}.log")

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("Vstup2026")

def log_info(message):
    """Логує інформаційне повідомлення."""
    logger.info(message)

def log_error(message, exception=None):
    """Логує повідомлення про помилку та виняток (якщо є)."""
    if exception:
        logger.error(f"{message} | Exception: {str(exception)}", exc_info=True)
    else:
        logger.error(message)

def log_warning(message):
    """Логує попередження."""
    logger.warning(message)
