#!/usr/bin/env python3
"""
E1 — Script de coleta automatizada | Sprint 3 | Projeto Integrador BIINAR
Sistema de Inteligência Tributária — Dívida Ativa de Palmas-TO (Sefin)

O que este script evidencia (rubrica E1):
  1. AUTENTICAÇÃO   -> token lido de variável de ambiente (nunca no código).
  2. PAGINAÇÃO      -> laço página a página (page/size), com parada por página
                       vazia, por última página ou por link "next".
  3. RATE LIMIT     -> limitador de janela deslizante (máx. N req / janela) +
                       respeito a HTTP 429 e ao cabeçalho Retry-After.
  4. DELAY          -> pausa fixa + jitter aleatório entre TODAS as requisições.
  5. ÉTICA          -> checagem de robots.txt, User-Agent identificado, fonte oficial.
  6. BRUTO DATADO   -> JSON bruto preservado em data/bruto/<fonte>_<AAAA-MM-DD>.json
                       + manifesto com hash SHA-256 e contagem de registros.

Execução (exemplo):
  export PALMAS_API_BASE="https://<host-oficial-da-api>"
  export PALMAS_API_TOKEN="<seu-token>"
  python coleta.py --endpoint /divida-ativa --fonte divida_ativa
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO (ajuste aqui ou via variáveis de ambiente)
# ----------------------------------------------------------------------------
API_BASE = os.getenv("PALMAS_API_BASE", "").rstrip("/")
API_TOKEN = os.getenv("PALMAS_API_TOKEN", "")

USER_AGENT = "BIINAR-UFT-PI-Sefin/1.0 (projeto academico; contato: equipe@exemplo.edu.br)"

# --- Paginação ---
PAGE_PARAM = "page"          # nome do parâmetro de página na API
SIZE_PARAM = "size"          # nome do parâmetro de tamanho da página
PAGE_SIZE = 500              # registros por página
FIRST_PAGE = 1               # algumas APIs começam em 0
MAX_PAGES = 10_000           # trava de segurança contra laço infinito
RECORDS_KEY = "data"         # chave do JSON que contém a lista (None = resposta já é lista)

# --- Rate limit (janela deslizante) ---
RATE_LIMIT_MAX_REQUESTS = 30     # no máximo 30 requisições...
RATE_LIMIT_WINDOW_SECONDS = 60   # ...a cada 60 segundos

# --- Delay entre requisições ---
DELAY_BASE_SECONDS = 1.0     # pausa fixa mínima entre requisições
DELAY_JITTER_SECONDS = 0.5   # + aleatório de 0 a 0,5 s (evita padrão de robô)

# --- Robustez ---
TIMEOUT_SECONDS = 30
MAX_RETRIES = 5
BACKOFF_FACTOR = 2.0         # espera exponencial: 2s, 4s, 8s, 16s, 32s

DIR_BRUTO = Path("data/bruto")
DIR_LOGS = Path("logs")

log = logging.getLogger("coleta")


# ----------------------------------------------------------------------------
# RATE LIMITER — janela deslizante
# ----------------------------------------------------------------------------
class RateLimiter:
    """Garante no máximo `max_requests` chamadas em qualquer janela de
    `window` segundos. Se o limite for atingido, BLOQUEIA (dorme) até
    que a requisição mais antiga saia da janela."""

    def __init__(self, max_requests: int, window: float):
        self.max_requests = max_requests
        self.window = window
        self._stamps: deque[float] = deque()

    def wait(self) -> None:
        agora = time.monotonic()
        # descarta marcas fora da janela
        while self._stamps and agora - self._stamps[0] >= self.window:
            self._stamps.popleft()

        if len(self._stamps) >= self.max_requests:
            espera = self.window - (agora - self._stamps[0]) + 0.05
            log.info(
                "RATE LIMIT local atingido (%d req/%ds). Aguardando %.1fs...",
                self.max_requests, self.window, espera,
            )
            time.sleep(max(espera, 0))
            return self.wait()  # reavalia a janela após dormir

        self._stamps.append(time.monotonic())


def delay_entre_requisicoes() -> None:
    """DELAY explícito: pausa fixa + jitter entre requisições."""
    pausa = DELAY_BASE_SECONDS + random.uniform(0, DELAY_JITTER_SECONDS)
    log.debug("Delay de %.2fs antes da próxima requisição.", pausa)
    time.sleep(pausa)


# ----------------------------------------------------------------------------
# SESSÃO HTTP com autenticação e retry
# ----------------------------------------------------------------------------
def criar_sessao() -> requests.Session:
    if not API_BASE:
        sys.exit("ERRO: defina a variável de ambiente PALMAS_API_BASE.")
    if not API_TOKEN:
        sys.exit("ERRO: defina a variável de ambiente PALMAS_API_TOKEN.")

    sessao = requests.Session()
    sessao.headers.update({
        "Authorization": f"Bearer {API_TOKEN}",  # AUTENTICAÇÃO
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    })

    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=(500, 502, 503, 504),  # 429 tratado manualmente abaixo
        allowed_methods=("GET",),
        respect_retry_after_header=True,
    )
    sessao.mount("https://", HTTPAdapter(max_retries=retry))
    sessao.mount("http://", HTTPAdapter(max_retries=retry))
    return sessao


# ----------------------------------------------------------------------------
# ÉTICA — robots.txt
# ----------------------------------------------------------------------------
def permitido_por_robots(url_completa: str) -> bool:
    """Consulta o robots.txt do host. Se não existir/falhar, assume permitido
    (comportamento padrão do urllib), mas registra no log."""
    p = urlparse(url_completa)
    robots_url = f"{p.scheme}://{p.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception as e:  # noqa: BLE001
        log.warning("Não foi possível ler %s (%s). Prosseguindo com cautela.", robots_url, e)
        return True
    ok = rp.can_fetch(USER_AGENT, url_completa)
    log.info("robots.txt (%s): acesso %s", robots_url, "PERMITIDO" if ok else "NEGADO")
    return ok


# ----------------------------------------------------------------------------
# REQUISIÇÃO ÚNICA — combina rate limit + delay + tratamento de 429
# ----------------------------------------------------------------------------
def requisitar(sessao: requests.Session, limiter: RateLimiter,
               url: str, params: dict | None = None) -> requests.Response:
    tentativas_429 = 0
    while True:
        limiter.wait()               # (1) RATE LIMIT local
        resp = sessao.get(url, params=params, timeout=TIMEOUT_SECONDS)
        delay_entre_requisicoes()    # (2) DELAY após cada chamada

        if resp.status_code == 429:  # (3) RATE LIMIT imposto pelo servidor
            tentativas_429 += 1
            if tentativas_429 > MAX_RETRIES:
                resp.raise_for_status()
            retry_after = resp.headers.get("Retry-After")
            try:
                espera = float(retry_after) if retry_after else BACKOFF_FACTOR ** tentativas_429
            except ValueError:
                espera = BACKOFF_FACTOR ** tentativas_429
            log.warning("HTTP 429 do servidor. Aguardando %.1fs (tentativa %d/%d).",
                        espera, tentativas_429, MAX_RETRIES)
            time.sleep(espera)
            continue

        if resp.status_code in (401, 403):
            sys.exit(f"ERRO de autenticação/autorização (HTTP {resp.status_code}). Verifique o token.")

        resp.raise_for_status()
        return resp


# ----------------------------------------------------------------------------
# PAGINAÇÃO
# ----------------------------------------------------------------------------
def extrair_registros(payload) -> list:
    if RECORDS_KEY is None:
        return payload if isinstance(payload, list) else []
    if isinstance(payload, dict):
        return payload.get(RECORDS_KEY, []) or []
    return []


def coletar_paginado(sessao: requests.Session, limiter: RateLimiter,
                     url: str, params_extra: dict | None = None) -> list:
    """Percorre TODAS as páginas do endpoint.

    Critérios de parada (qualquer um):
      - página vazia;
      - página com menos registros que PAGE_SIZE (última página);
      - JSON indica total de páginas e já chegamos nele;
      - atingiu MAX_PAGES (trava de segurança).
    """
    todos: list = []
    pagina = FIRST_PAGE
    total_paginas = None

    while pagina < FIRST_PAGE + MAX_PAGES:
        params = {PAGE_PARAM: pagina, SIZE_PARAM: PAGE_SIZE, **(params_extra or {})}
        resp = requisitar(sessao, limiter, url, params)
        payload = resp.json()
        registros = extrair_registros(payload)

        # descobre total de páginas se a API informar (ajuste às chaves reais)
        if isinstance(payload, dict) and total_paginas is None:
            total_paginas = payload.get("total_pages") or payload.get("totalPages")

        log.info("PAGINAÇÃO: página %s%s -> %d registros (acumulado: %d)",
                 pagina,
                 f"/{total_paginas}" if total_paginas else "",
                 len(registros), len(todos) + len(registros))

        if not registros:
            log.info("Página vazia: fim da paginação.")
            break

        todos.extend(registros)

        if len(registros) < PAGE_SIZE:
            log.info("Última página (menos de %d registros).", PAGE_SIZE)
            break
        if total_paginas and pagina >= FIRST_PAGE + int(total_paginas) - 1:
            log.info("Alcançado o total de páginas informado pela API.")
            break

        pagina += 1
    else:
        log.warning("MAX_PAGES (%d) atingido — verifique se a API paginou corretamente.", MAX_PAGES)

    return todos


# ----------------------------------------------------------------------------
# PERSISTÊNCIA — bruto preservado e datado
# ----------------------------------------------------------------------------
def salvar_bruto(registros: list, fonte: str, endpoint: str, inicio: datetime) -> Path:
    DIR_BRUTO.mkdir(parents=True, exist_ok=True)
    data = inicio.strftime("%Y-%m-%d")
    caminho = DIR_BRUTO / f"{fonte}_{data}.json"

    # nunca sobrescreve um bruto já preservado no mesmo dia
    if caminho.exists():
        caminho = DIR_BRUTO / f"{fonte}_{inicio.strftime('%Y-%m-%d_%H%M%S')}.json"

    conteudo = json.dumps(registros, ensure_ascii=False, indent=2).encode("utf-8")
    caminho.write_bytes(conteudo)

    manifesto = {
        "fonte": fonte,
        "endpoint": endpoint,
        "coletado_em": inicio.isoformat(timespec="seconds"),
        "arquivo": caminho.name,
        "n_registros": len(registros),
        "sha256": hashlib.sha256(conteudo).hexdigest(),
        "parametros": {
            "page_size": PAGE_SIZE,
            "rate_limit": f"{RATE_LIMIT_MAX_REQUESTS} req/{RATE_LIMIT_WINDOW_SECONDS}s",
            "delay": f"{DELAY_BASE_SECONDS}s + jitter ate {DELAY_JITTER_SECONDS}s",
        },
    }
    (caminho.with_suffix(".manifesto.json")).write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("Bruto salvo em %s (%d registros, sha256=%s...)",
             caminho, len(registros), manifesto["sha256"][:12])
    return caminho


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
def configurar_logs() -> None:
    DIR_LOGS.mkdir(exist_ok=True)
    arquivo = DIR_LOGS / f"coleta_{datetime.now():%Y-%m-%d_%H%M%S}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[logging.FileHandler(arquivo, encoding="utf-8"), logging.StreamHandler()],
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="E1 — Coleta automatizada via API (Sefin Palmas)")
    ap.add_argument("--endpoint", required=True, help="caminho do endpoint, ex.: /divida-ativa")
    ap.add_argument("--fonte", required=True, help="nome curto da fonte, ex.: divida_ativa")
    args = ap.parse_args()

    configurar_logs()
    inicio = datetime.now()
    t0 = time.monotonic()

    sessao = criar_sessao()
    url = urljoin(API_BASE + "/", args.endpoint.lstrip("/"))

    if not permitido_por_robots(url):
        sys.exit("Coleta abortada: robots.txt nega acesso a este caminho.")

    limiter = RateLimiter(RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)

    log.info("Iniciando coleta: %s | page_size=%d | rate=%d req/%ds | delay=%.1fs+jitter %.1fs",
             url, PAGE_SIZE, RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS,
             DELAY_BASE_SECONDS, DELAY_JITTER_SECONDS)

    registros = coletar_paginado(sessao, limiter, url)
    salvar_bruto(registros, args.fonte, args.endpoint, inicio)

    log.info("Coleta concluída em %.1fs — %d registros.", time.monotonic() - t0, len(registros))


if __name__ == "__main__":
    main()
