import os

from dotenv import load_dotenv

from shimeji_nexus.ai import providers

load_dotenv(override=True)

PROVIDER_KEY_MAP = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

MODEL_MAP = {
    "gemini": "gemini-flash-lite-latest",
    "openai": "gpt-4o-mini",
    "openrouter": "openai/gpt-4o-mini",
}

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

PROVEEDORES = {
    "gemini": ("Gemini", "GEMINI_API_KEY", "https://aistudio.google.com/apikey"),
    "openai": ("OpenAI", "OPENAI_API_KEY", "https://platform.openai.com/api-keys"),
    "openrouter": ("OpenRouter", "OPENROUTER_API_KEY", "https://openrouter.ai/keys"),
}

MENSAJE_SIN_CLAVE = "Falta tu clave de IA. Agrégala en Ajustes > Inteligencia artificial."


def _leer_provider():
    return os.getenv("AI_PROVIDER", "gemini").strip().lower()


def _leer_key(provider):
    env_var = PROVIDER_KEY_MAP.get(provider)
    return os.getenv(env_var, "") if env_var else ""


def _completar(provider, api_key, system_prompt, user_content, max_tokens):
    if provider == "gemini":
        prompt = f"{system_prompt} {user_content}"
        return providers.gemini(prompt, api_key, MODEL_MAP["gemini"])
    if provider == "openai":
        return providers.chat_completion(None, MODEL_MAP["openai"], api_key, system_prompt, user_content, max_tokens)
    if provider == "openrouter":
        return providers.chat_completion(OPENROUTER_BASE_URL, MODEL_MAP["openrouter"], api_key, system_prompt, user_content, max_tokens)
    return None


def generar_texto(system_prompt, user_text, max_palabras=12):
    provider = _leer_provider()
    api_key = _leer_key(provider)
    if not api_key:
        return MENSAJE_SIN_CLAVE
    user_content = f"El usuario dice: '{user_text}'. Responde corto ({max_palabras} palabras max) en espanol."
    try:
        resultado = _completar(provider, api_key, system_prompt, user_content, max_tokens=80)
        if resultado is None:
            return f"Proveedor '{provider}' no soportado"
        return resultado
    except Exception as e:
        return f"Error: {e}"


def generar_comentario_entorno(system_prompt, ventana_activa, max_palabras=10):
    provider = _leer_provider()
    api_key = _leer_key(provider)
    if not api_key:
        return MENSAJE_SIN_CLAVE
    user_content = f"El usuario esta viendo: '{ventana_activa}'. Comenta en personaje ({max_palabras} palabras max)."
    try:
        resultado = _completar(provider, api_key, system_prompt, user_content, max_tokens=60)
        if resultado is None:
            return f"Proveedor '{provider}' no soportado"
        return resultado
    except Exception as e:
        return f"Error: {e}"


def probar_clave(provider, api_key):
    """Hace una llamada minima para saber si la clave sirve. Devuelve (ok, mensaje)."""
    try:
        _completar(provider, api_key, "Eres un asistente.", "Responde solo con la palabra: ok", max_tokens=20)
        return True, "Conexión correcta. La clave funciona."
    except Exception as e:
        texto = str(e)
        if any(k in texto for k in ("401", "403", "UNAUTHENTICATED", "API key not valid", "Incorrect API key", "PERMISSION_DENIED")):
            return False, "La clave no es válida o no tiene permiso."
        if "429" in texto or "RESOURCE_EXHAUSTED" in texto:
            return False, "La clave es válida pero se agotó su cuota."
        if "503" in texto or "UNAVAILABLE" in texto:
            return False, "El servicio está saturado ahora. Prueba en un momento."
        return False, "No se pudo conectar: " + texto[:110]
