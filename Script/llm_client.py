import os

import httpx


OLLAMA_URL_PADRAO = "http://localhost:11434/api/generate"
OPENAI_BASE_URL_PADRAO = "https://api.openai.com/v1"
OPENAI_MODEL_PADRAO = "gpt-4.1-mini"


def extrair_texto_openai(resposta):
    if isinstance(resposta.get("output_text"), str):
        return resposta["output_text"].strip()

    textos = []
    for item in resposta.get("output", []):
        for conteudo in item.get("content", []):
            texto = conteudo.get("text")
            if isinstance(texto, str):
                textos.append(texto)

    return "\n".join(textos).strip()


async def gerar_texto(
    prompt_usuario,
    system_prompt,
    provedor="ollama",
    modelo=None,
    ollama_url=None,
    openai_api_key=None,
    openai_model=None,
    openai_base_url=None,
):
    if provedor == "ollama":
        return await gerar_texto_ollama(
            prompt_usuario=prompt_usuario,
            system_prompt=system_prompt,
            modelo=modelo,
            ollama_url=ollama_url,
        )

    if provedor == "openai":
        return await gerar_texto_openai(
            prompt_usuario=prompt_usuario,
            system_prompt=system_prompt,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            openai_base_url=openai_base_url,
        )

    raise ValueError(f"Provedor LLM nao suportado: {provedor}")


async def gerar_texto_ollama(prompt_usuario, system_prompt, modelo=None, ollama_url=None):
    modelo = modelo or os.getenv("OLLAMA_MODEL", "")
    ollama_url = ollama_url or os.getenv("OLLAMA_URL", OLLAMA_URL_PADRAO)

    if not modelo:
        raise ValueError("Modelo Ollama nao informado.")

    payload = {
        "model": modelo,
        "prompt": prompt_usuario,
        "system": system_prompt,
        "format": "json",
        "options": {
            "temperature": 0.1,
        },
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        resposta = await client.post(ollama_url, json=payload)
        resposta.raise_for_status()
        return resposta.json().get("response", "").strip()


async def gerar_texto_openai(
    prompt_usuario,
    system_prompt,
    openai_api_key=None,
    openai_model=None,
    openai_base_url=None,
):
    openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    openai_model = openai_model or os.getenv("OPENAI_MODEL", OPENAI_MODEL_PADRAO)
    openai_base_url = (openai_base_url or os.getenv("OPENAI_BASE_URL", OPENAI_BASE_URL_PADRAO)).rstrip("/")

    if not openai_api_key:
        raise ValueError("Chave OpenAI nao informada. Use OPENAI_API_KEY ou --openai-api-key.")

    payload = {
        "model": openai_model,
        "input": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt_usuario,
            },
        ],
        "text": {
            "format": {
                "type": "json_object",
            },
        },
    }

    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        resposta = await client.post(f"{openai_base_url}/responses", json=payload, headers=headers)
        resposta.raise_for_status()
        return extrair_texto_openai(resposta.json())
