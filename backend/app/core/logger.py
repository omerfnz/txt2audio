"""
Merkezi logging yapılandırması.
Tüm proje genelinde tutarlı logging sağlar.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Logger oluşturur ve yapılandırır.
    
    Args:
        name: Logger adı (genellikle __name__)
        log_file: Log dosyası yolu (opsiyonel)
        level: Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console: Konsola da yazdır mı?
    
    Returns:
        Yapılandırılmış logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(str(log_path))
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Default logger - always log under the backend/logs directory,
# independent of the current working directory.
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # points to backend/
DEFAULT_LOG_FILE = BASE_DIR / "logs" / "app.log"

default_logger = setup_logger(
    "ai_audiobook_studio",
    log_file=str(DEFAULT_LOG_FILE),
    level=logging.INFO,
)
