import collections
import datetime
import logging
import sys
import threading
from typing import List, Dict, Optional

class SystemLogService:
    """
    Serviço de captura e buffer de logs em memória para permitir que a interface
    (aba Configurações > Logs do Sistema) visualize o que acontece na API em tempo real
    (especialmente no Render em produção, sem precisar acessar o terminal de infraestrutura).
    """

    def __init__(self, max_records: int = 600):
        self._buffer: collections.deque = collections.deque(maxlen=max_records)
        self._lock = threading.Lock()
        self._installed = False

    def add_log(self, message: str, level: str = "INFO", category: str = "geral"):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "timestamp": now_str,
            "level": level.upper(),
            "category": category,
            "message": message.strip()
        }
        with self._lock:
            self._buffer.append(record)

    def get_logs(self, limit: int = 250, level: Optional[str] = None, search: Optional[str] = None) -> List[Dict]:
        with self._lock:
            logs = list(self._buffer)

        if level and level.upper() != "ALL":
            logs = [l for l in logs if l["level"] == level.upper()]

        if search:
            s_lower = search.lower()
            logs = [l for l in logs if s_lower in l["message"].lower()]

        return logs[-limit:]

    def clear(self):
        with self._lock:
            self._buffer.clear()

    def install_handler(self):
        """Acopla um handler no logging padrão do Python para capturar logs do Uvicorn e da aplicação."""
        if self._installed:
            return

        service_instance = self

        class BufferLoggingHandler(logging.Handler):
            def emit(self, record):
                try:
                    msg = self.format(record)
                    # Classifica a categoria com base no texto
                    category = "geral"
                    upper_msg = msg.upper()
                    if any(k in upper_msg for k in ["METRICS", "BUSCA", "SEARCH", "PROVEDOR"]):
                        category = "busca"
                    elif any(k in upper_msg for k in ["AUTH", "LOGIN", "KEYCLOAK", "TOKEN"]):
                        category = "auth"
                    elif any(k in upper_msg for k in ["ERROR", "FALHA", "EXCEPTION", "TRACEBACK"]):
                        category = "erro"
                    elif "DATABASE" in upper_msg or "SEED" in upper_msg:
                        category = "banco"

                    service_instance.add_log(msg, level=record.levelname, category=category)
                except Exception:
                    pass

        handler = BufferLoggingHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)

        # Adiciona aos loggers relevantes
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        app_logger = logging.getLogger("aplicacao_new")
        app_logger.addHandler(handler)

        uvicorn_logger = logging.getLogger("uvicorn")
        uvicorn_logger.addHandler(handler)

        uvicorn_access = logging.getLogger("uvicorn.access")
        uvicorn_access.addHandler(handler)

        self._installed = True
        self.add_log("Serviço de buffer de logs ativado com sucesso.", level="INFO", category="banco")


log_service = SystemLogService()
