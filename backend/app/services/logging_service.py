import os
import logging
from logging.handlers import RotatingFileHandler

class LoggingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggingService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Define diretório de logs
        self.log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        self.log_file = os.path.join(self.log_dir, "app.log")

        # Configuração do Logger
        self.logger = logging.getLogger("aplicacao_new")
        self.logger.setLevel(logging.INFO)

        # Formato: 2024-04-29 15:00:00 - CATEGORIA - MENSAGEM
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Handler para Arquivo (Rotativo: 5MB cada, mantém os últimos 5)
        file_handler = RotatingFileHandler(
            self.log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Handler para Console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def log(self, level, category, message):
        """
        Registra um log com categoria específica.
        Ex: logger.log(logging.INFO, "SCRAPER", "TSA iniciada")
        """
        msg = f"[{category}] {message}"
        if level == logging.INFO:
            self.logger.info(msg)
        elif level == logging.WARNING:
            self.logger.warning(msg)
        elif level == logging.ERROR:
            self.logger.error(msg)
        elif level == logging.DEBUG:
            self.logger.debug(msg)

    def info(self, category, message):
        self.log(logging.INFO, category, message)

    def warning(self, category, message):
        self.log(logging.WARNING, category, message)

    def error(self, category, message):
        self.log(logging.ERROR, category, message)

# Singleton global instance
logger = LoggingService()
