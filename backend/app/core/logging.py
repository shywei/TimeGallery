import logging
import sys
from pathlib import Path
from backend.app.core.config import settings

def setup_logging():
    log_dir = settings.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    app_log_file = log_dir / "application.log"
    scanner_log_file = log_dir / "scanner.log"
    error_log_file = log_dir / "error.log"

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # File Handler for Application
    app_handler = logging.FileHandler(app_log_file, encoding="utf-8")
    app_handler.setFormatter(formatter)
    app_handler.setLevel(logging.INFO)
    root_logger.addHandler(app_handler)

    # File Handler for Errors
    error_handler = logging.FileHandler(error_log_file, encoding="utf-8")
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    return root_logger
