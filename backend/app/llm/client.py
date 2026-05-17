from __future__ import annotations

import json
from loguru import logger
import httpx

from app.core.config import settings


async def generate(prompt: str, system: str = "") -> str:
    if settings.LLM_PROVIDER == "openai":
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            res = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
            )
            return res.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI generate failed: {e}")
            return ""

    # default: ollama
    try:
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
    except Exception as e:
        logger.error(f"Ollama generate failed: {e}")
        return ""


def parse_llm_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        return {}
