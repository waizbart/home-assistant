"""
Monta o prompt completo enviado ao gpt-4o-mini para gerar o briefing.
"""

import json
from datetime import datetime
from typing import Optional

WEEKDAY_PT = [
    "Segunda-feira", "Terça-feira", "Quarta-feira",
    "Quinta-feira", "Sexta-feira", "Sábado", "Domingo",
]

MONTH_PT = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]

SYSTEM_PROMPT = """Você é um assistente de alarme matinal. Sua tarefa é gerar um briefing de voz em português (pt-BR) com base nos dados fornecidos.

REGRAS OBRIGATÓRIAS:
- Escreva entre 350 e 500 palavras no total.
- Tom direto, sem motivação forçada, sem frases de efeito, sem emojis.
- O texto deve ser fluido para ser lido em voz alta — não é uma lista, é uma fala natural.
- Siga a estrutura: Abertura → Clima → Agenda → Mercado → Notícias.
- Se um bloco estiver ausente nos dados (ex: agenda indisponível), pule-o naturalmente.
- Para notícias: receba os títulos brutos e decida quais valem mencionar e como resumir — priorize tech/dev para o Hacker News, e apenas notícias fora do comum do G1.
- Nunca invente dados. Se não tiver informação, simplesmente não mencione aquele ponto.
- Não diga "Bloco 1", "Bloco 2" etc. O texto deve ser contínuo."""


def build(
    weather: Optional[dict],
    events: Optional[list],
    market: Optional[dict],
    news: Optional[dict],
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for the OpenAI chat call.
    """
    now = datetime.now()
    weekday = WEEKDAY_PT[now.weekday()]
    date_str = f"{weekday}, {now.day} de {MONTH_PT[now.month]} de {now.year}"

    sections = [f"DATA E HORA ATUAL: {date_str}, {now.strftime('%H:%M')}"]

    # Clima
    if weather:
        sections.append(_format_weather(weather))
    else:
        sections.append("CLIMA: dados indisponíveis — omita este bloco.")

    # Agenda
    if events is not None:
        sections.append(_format_events(events))
    else:
        sections.append("AGENDA: dados indisponíveis — omita este bloco.")

    # Mercado
    if market:
        sections.append(_format_market(market))
    else:
        sections.append("MERCADO: dados indisponíveis — omita este bloco.")

    # Notícias
    if news:
        sections.append(_format_news(news))
    else:
        sections.append("NOTÍCIAS: dados indisponíveis — omita este bloco.")

    user_prompt = "\n\n".join(sections)
    user_prompt += "\n\nGere o briefing agora."

    return SYSTEM_PROMPT, user_prompt


def _format_weather(w: dict) -> str:
    lines = ["CLIMA (Sorocaba, SP):"]
    lines.append(f"- Temperatura atual: {w['current_temp']}°C")
    lines.append(f"- Mínima / Máxima do dia: {w['temp_min']}°C / {w['temp_max']}°C")
    lines.append(f"- Descrição: {w['description']}")

    diff = abs(w["current_temp"] - w["feels_like"])
    if diff >= 5:
        lines.append(f"- Sensação térmica: {w['feels_like']}°C (diferença relevante de {round(diff, 1)}°C)")

    if w.get("rain_windows"):
        for rw in w["rain_windows"]:
            lines.append(f"- Chuva prevista entre {rw['start']} e {rw['end']} (probabilidade {int(rw['prob'] * 100)}%)")
    else:
        lines.append("- Sem previsão de chuva significativa.")

    if w.get("wind_speed_kmh", 0) >= 40:
        lines.append(f"- ALERTA: vento forte a {w['wind_speed_kmh']} km/h.")

    if w.get("alerts"):
        for alert in w["alerts"]:
            lines.append(f"- ALERTA METEOROLÓGICO: {alert}")

    return "\n".join(lines)


def _format_events(events: list) -> str:
    if not events:
        return "AGENDA: nenhum evento hoje. Dia livre."

    lines = [f"AGENDA DO DIA ({len(events)} evento(s)):"]
    for ev in events:
        if ev["all_day"]:
            lines.append(f"- [Dia todo] {ev['title']}")
        else:
            duration = f" ({ev['duration_min']} min)" if ev["duration_min"] else ""
            location = f" — {ev['location']}" if ev.get("location") else ""
            lines.append(f"- {ev['start']} às {ev['end']}: {ev['title']}{duration}{location}")

    return "\n".join(lines)


def _format_market(m: dict) -> str:
    lines = ["MERCADO FINANCEIRO:"]

    if "usd_brl" in m:
        rate = m["usd_brl"]
        change = m.get("usd_brl_change_pct")
        if change is not None:
            direction = "alta" if change > 0 else "queda"
            lines.append(f"- USD/BRL: R$ {rate:.2f} ({direction} de {abs(change):.1f}% em relação a ontem)")
        else:
            lines.append(f"- USD/BRL: R$ {rate:.2f}")

    if "ibov_close" in m:
        ibov = m["ibov_close"]
        change = m.get("ibov_change_pct")
        if change is not None:
            direction = "alta" if change > 0 else "queda"
            marker = " (movimento relevante)" if m.get("ibov_relevant_move") else ""
            lines.append(f"- IBOVESPA (fechamento anterior): {ibov:,.0f} pontos ({direction} de {abs(change):.1f}%){marker}")
        else:
            lines.append(f"- IBOVESPA (fechamento anterior): {ibov:,.0f} pontos")

    return "\n".join(lines)


def _format_news(n: dict) -> str:
    lines = ["NOTÍCIAS BRUTAS (filtre e resuma apenas o que for relevante):"]

    hn_items = n.get("hacker_news", [])
    if hn_items:
        lines.append("Hacker News (top stories):")
        for item in hn_items:
            lines.append(f"  - [{item['score']} pts] {item['title']}")

    g1_items = n.get("g1", [])
    if g1_items:
        lines.append("G1 Brasil (RSS):")
        for item in g1_items:
            lines.append(f"  - {item['title']}")

    lines.append("Instrução: mencione no máximo 2 do HN (priorize tech/dev) e 1 do G1 apenas se for fora do comum. Não leia os títulos literalmente — resuma em linguagem natural.")

    return "\n".join(lines)
