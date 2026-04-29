import json
import logging
import re
import httpx
from openai import AsyncOpenAI
import google.generativeai as genai

from utils.config import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI accountant assistant that parses financial transaction inputs in Uzbek and Russian languages.

Given a user message about a financial transaction, extract:
1. "amount" (number, in UZS unless specified otherwise)
2. "item" (what was bought/sold/received — short description)
3. "category" (one of: Oziq-ovqat, Transport, Kommunal, Maosh, Ijara, Tovar, Xizmat, Soliq, Boshqa)
4. "description" (brief note about the transaction)
5. "currency" (default "UZS")

IMPORTANT:
- "non" means bread in Uzbek
- "sotdim" = sold, "oldim" = bought, "to'ladim" = paid, "oldim" = received
- Parse numbers with spaces or commas (e.g., "500 000" = 500000, "1,000,000" = 1000000)
- If amount has "mln" or "million", multiply accordingly
- If the text is unclear, make your best guess

Respond ONLY with valid JSON, no markdown formatting:
{"amount": <number>, "item": "<string>", "category": "<string>", "description": "<string>", "currency": "UZS"}
"""

TAX_SYSTEM_PROMPT = """You are an AI tax advisor for small businesses in Uzbekistan.

You know Uzbekistan tax law:
- Simplified tax (yagona soliq): 4% of gross revenue for most small businesses
- VAT (QQS): 12% (mandatory if revenue > 1 billion UZS/year)
- Social tax: 12% of payroll
- Income tax (JSMJ): 12% on profits for larger businesses
- Individual income tax: 12%

Given the business financial summary, provide:
1. Estimated tax liability breakdown
2. Tax optimization tips (legal)
3. Upcoming deadlines/recommendations

Respond in Uzbek language. Be specific with numbers.
"""


async def parse_transaction(text: str) -> dict | None:
    """Parse a natural language transaction input using AI."""
    try:
        if config.AI_PROVIDER == "claude":
            return await _parse_with_claude(text)
        elif config.AI_PROVIDER == "gemini":
            return await _parse_with_gemini(text)
        return await _parse_with_openai(text)
    except Exception as e:
        logger.error(f"AI parsing failed: {e}")
        return _fallback_parse(text)


async def _parse_with_openai(text: str) -> dict | None:
    client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0.1,
        max_tokens=300,
    )
    content = response.choices[0].message.content or ""
    return _clean_json_response(content)


async def _parse_with_gemini(text: str) -> dict | None:
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=config.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT
    )
    response = await model.generate_content_async(text)
    return _clean_json_response(response.text)


async def _parse_with_claude(text: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": config.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": config.ANTHROPIC_MODEL,
                "max_tokens": 300,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": text}],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        content = data["content"][0]["text"].strip()
        return _clean_json_response(content)


def _clean_json_response(content: str) -> dict | None:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def _fallback_parse(text: str) -> dict | None:
    """Regex-based fallback when AI is unavailable."""
    amount_match = re.search(r"([\d\s,]+(?:\.\d+)?)", text.replace(" ", ""))
    if not amount_match:
        amount_match = re.search(r"(\d[\d\s,]*\d)", text)

    if not amount_match:
        return None

    raw_amount = amount_match.group(1).replace(" ", "").replace(",", "")
    try:
        amount = float(raw_amount)
    except ValueError:
        return None

    text_lower = text.lower()
    category_map = {
        "non": "Oziq-ovqat", "go'sht": "Oziq-ovqat", "sabzavot": "Oziq-ovqat",
        "oziq": "Oziq-ovqat", "ovqat": "Oziq-ovqat", "benzin": "Transport",
        "taxi": "Transport", "transport": "Transport", "gaz": "Kommunal",
        "elektr": "Kommunal", "suv": "Kommunal", "kommunal": "Kommunal",
        "maosh": "Maosh", "ish haqqi": "Maosh", "ijara": "Ijara",
        "arenda": "Ijara", "soliq": "Soliq", "tovar": "Tovar",
    }

    category = "Boshqa"
    for keyword, cat in category_map.items():
        if keyword in text_lower:
            category = cat
            break

    item = re.sub(r"/\w+\s*", "", text)
    item = re.sub(r"[\d\s,]+(?:\.\d+)?", "", item).strip()
    item = item[:100] if item else "Noma'lum"

    return {
        "amount": amount, "item": item, "category": category,
        "description": text, "currency": "UZS"
    }


async def get_tax_advice(summary: dict) -> str:
    """Get AI-driven tax calculation and advice."""
    prompt = f"""Biznes moliyaviy ma'lumotlari:
- Jami daromad: {summary['total_income']:,.0f} UZS
- Jami xarajat: {summary['total_expense']:,.0f} UZS
- Sof foyda: {summary['net_profit']:,.0f} UZS
- Tranzaksiyalar soni: {summary['transaction_count']}

Iltimos, soliq hisobini va maslahatlarni bering.
"""
    try:
        if config.AI_PROVIDER == "claude":
            return await _tax_advice_claude(prompt)
        elif config.AI_PROVIDER == "gemini":
            return await _tax_advice_gemini(prompt)
        return await _tax_advice_openai(prompt)
    except Exception as e:
        logger.error(f"Tax advice AI failed: {e}")
        return _fallback_tax_advice(summary)


async def _tax_advice_openai(prompt: str) -> str:
    client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "system", "content": TAX_SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000,
    )
    return response.choices[0].message.content or "Xatolik."


async def _tax_advice_gemini(prompt: str) -> str:
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name=config.GEMINI_MODEL, system_instruction=TAX_SYSTEM_PROMPT)
    response = await model.generate_content_async(prompt)
    return response.text


async def _tax_advice_claude(prompt: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": config.ANTHROPIC_MODEL, "max_tokens": 1000, "system": TAX_SYSTEM_PROMPT, "messages": [{"role": "user", "content": prompt}]},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]


def _fallback_tax_advice(summary: dict) -> str:
    income = summary["total_income"]
    simplified_tax = income * config.TAX_RATE_DEFAULT
    return f"📊 *Soliq hisobi (AI'siz):*\n💰 Jami daromad: {income:,.0f} UZS\n🏛 Yagona soliq (4%): {simplified_tax:,.0f} UZS"
