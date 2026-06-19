import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER_KEY_MAP = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

MODEL_MAP = {
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-4o-mini",
    "openrouter": "openai/gpt-4o-mini",
}

def _leer_provider():
    return os.getenv("AI_PROVIDER", "gemini").strip().lower()

def _leer_key(provider):
    env_var = PROVIDER_KEY_MAP.get(provider)
    return os.getenv(env_var, "") if env_var else ""

def generar_texto(system_prompt, user_text, max_palabras=12):
    provider = _leer_provider()
    api_key = _leer_key(provider)
    if not api_key:
        return "Error: API key no configurada"
    prompt = f"{system_prompt} El usuario dice: '{user_text}'. Responde corto ({max_palabras} palabras max) en espanol."
    try:
        if provider == "gemini":
            return _gemini(prompt, api_key)
        elif provider == "openai":
            return _openai(system_prompt, user_text, api_key, max_palabras)
        elif provider == "openrouter":
            return _openrouter(system_prompt, user_text, api_key, max_palabras)
        else:
            return f"Proveedor '{provider}' no soportado"
    except Exception as e:
        return f"Error: {e}"

def generar_comentario_entorno(system_prompt, ventana_activa, max_palabras=10):
    provider = _leer_provider()
    api_key = _leer_key(provider)
    if not api_key:
        return "Error: API key no configurada"
    prompt = f"{system_prompt} El usuario ve: '{ventana_activa}'. Comenta en personaje ({max_palabras} palabras max)."
    try:
        if provider == "gemini":
            return _gemini(prompt, api_key)
        elif provider == "openai":
            return _openai_env(system_prompt, ventana_activa, api_key, max_palabras)
        elif provider == "openrouter":
            return _openrouter_env(system_prompt, ventana_activa, api_key, max_palabras)
        else:
            return f"Proveedor '{provider}' no soportado"
    except Exception as e:
        return f"Error: {e}"

def _gemini(prompt, api_key):
    from google import genai
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text.strip().replace('"', "")

def _openai(system_prompt, user_text, api_key, max_palabras):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Responde corto ({max_palabras} palabras max) en espanol: {user_text}"},
        ],
        max_tokens=80,
    )
    return response.choices[0].message.content.strip().replace('"', "")

def _openai_env(system_prompt, ventana, api_key, max_palabras):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"El usuario esta viendo: '{ventana}'. Comenta en personaje ({max_palabras} palabras max)."},
        ],
        max_tokens=60,
    )
    return response.choices[0].message.content.strip().replace('"', "")

def _openrouter(system_prompt, user_text, api_key, max_palabras):
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Responde corto ({max_palabras} palabras max) en espanol: {user_text}"},
        ],
        max_tokens=80,
    )
    return response.choices[0].message.content.strip().replace('"', "")

def _openrouter_env(system_prompt, ventana, api_key, max_palabras):
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"El usuario esta viendo: '{ventana}'. Comenta en personaje ({max_palabras} palabras max)."},
        ],
        max_tokens=60,
    )
    return response.choices[0].message.text.strip().replace('"', "")
