"""
Coleta dados de mercado financeiro:
- USD/BRL via Banco Central do Brasil (PTAX — gratuito, sem chave)
- IBOVESPA via yfinance
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import requests

logger = logging.getLogger(__name__)

PTAX_URL = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)"
IBOV_TICKER = "^BVSP"

# Threshold for "relevant movement" mention
MOVEMENT_THRESHOLD = 1.5  # percent


def collect() -> Optional[dict]:
    """
    Returns market data dict or None on failure.

    {
        "usd_brl": 5.74,
        "usd_brl_change_pct": -0.3,
        "ibov_close": 128450.0,
        "ibov_change_pct": 1.1,
        "ibov_relevant_move": True
    }
    """
    usd = _fetch_ptax()
    ibov = _fetch_ibovespa()

    if usd is None and ibov is None:
        return None

    result = {}
    if usd:
        result.update(usd)
    if ibov:
        result.update(ibov)

    return result if result else None


def _fetch_ptax() -> Optional[dict]:
    """Fetches USD/BRL from BCB PTAX API. Falls back to previous business day if today is unavailable."""
    for days_back in range(0, 5):
        target = datetime.now() - timedelta(days=days_back)
        if target.weekday() >= 5:  # skip weekends
            continue
        date_str = target.strftime("%m-%d-%Y")
        try:
            resp = requests.get(
                PTAX_URL,
                params={
                    "@dataCotacao": f"'{date_str}'",
                    "$format": "json",
                    "$select": "cotacaoCompra,cotacaoVenda,dataHoraCotacao",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json().get("value", [])
            if data:
                # Use last available rate of the day
                last = data[-1]
                rate = round((last["cotacaoCompra"] + last["cotacaoVenda"]) / 2, 4)

                # Try to get previous day's rate for change calculation
                prev_rate = _fetch_ptax_previous(target)
                change_pct = None
                if prev_rate:
                    change_pct = round(((rate - prev_rate) / prev_rate) * 100, 2)

                return {"usd_brl": rate, "usd_brl_change_pct": change_pct}
        except Exception as exc:
            logger.warning("PTAX fetch failed for %s: %s", date_str, exc)

    return None


def _fetch_ptax_previous(reference: datetime) -> Optional[float]:
    """Fetches the previous business day's USD/BRL rate."""
    for days_back in range(1, 5):
        target = reference - timedelta(days=days_back)
        if target.weekday() >= 5:
            continue
        date_str = target.strftime("%m-%d-%Y")
        try:
            resp = requests.get(
                PTAX_URL,
                params={
                    "@dataCotacao": f"'{date_str}'",
                    "$format": "json",
                    "$select": "cotacaoCompra,cotacaoVenda",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json().get("value", [])
            if data:
                last = data[-1]
                return round((last["cotacaoCompra"] + last["cotacaoVenda"]) / 2, 4)
        except Exception:
            pass
    return None


def _fetch_ibovespa() -> Optional[dict]:
    try:
        import yfinance as yf

        ticker = yf.Ticker(IBOV_TICKER)
        hist = ticker.history(period="5d")

        if hist.empty or len(hist) < 2:
            return None

        prev_close = float(hist["Close"].iloc[-2])
        last_close = float(hist["Close"].iloc[-1])
        change_pct = round(((last_close - prev_close) / prev_close) * 100, 2)

        return {
            "ibov_close": round(last_close, 0),
            "ibov_change_pct": change_pct,
            "ibov_relevant_move": abs(change_pct) >= MOVEMENT_THRESHOLD,
        }
    except Exception as exc:
        logger.warning("IBOV fetch failed: %s", exc)
        return None
