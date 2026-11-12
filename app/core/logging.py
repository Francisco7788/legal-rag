"""Logger centralizado.

Configuração simples: formato ISO-8601, nível via env (DEBUG em dev,
INFO em prod). Todo módulo importa `from app.core.logging import logger`
em vez de chamar `logging.getLogger(__name__)` em cada arquivo.
"""
from __future__ import annotations

import logging
import sys

from app.core.config import get_settings

settings = get_settings()
level = logging.DEBUG if settings.debug else logging.INFO

logging.basicConfig(
    level=level,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger("rag_api")
