"""Autenticacao simples por Bearer token para a API local.

Estrategia minima:
- token unico configurado em config.yaml (`api.token_gestor`)
- decorator `requer_token` protege rotas sensiveis
- algumas rotas sao explicitamente publicas (ex: /certificados/<h>/verificar)
- se o token estiver vazio na config, a API aceita qualquer request
  (ambiente de desenvolvimento). Em producao o `setup.sh` gera um token.
"""
from __future__ import annotations

import hmac
import secrets
from functools import wraps
from typing import Callable

from flask import jsonify, request


def gerar_token() -> str:
    """Gera um token aleatorio (32 bytes em hex) para o setup."""
    return secrets.token_hex(32)


def requer_token(token_esperado: str) -> Callable:
    """Decorator: bloqueia rotas sem header `Authorization: Bearer <token>`.

    Se `token_esperado` estiver vazio, a checagem e desativada (dev).
    """
    def decor(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not token_esperado:
                return func(*args, **kwargs)
            cab = request.headers.get("Authorization", "")
            prefixo = "Bearer "
            if not cab.startswith(prefixo):
                return jsonify({"erro": "token ausente"}), 401
            fornecido = cab[len(prefixo):].strip()
            # Compara em tempo constante para nao vazar tamanho do token.
            if not hmac.compare_digest(fornecido, token_esperado):
                return jsonify({"erro": "token invalido"}), 401
            return func(*args, **kwargs)
        return wrapper
    return decor
