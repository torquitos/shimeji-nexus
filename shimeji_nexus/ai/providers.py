_RESPALDO_GEMINI = "gemini-3.5-flash-lite"


def gemini(prompt, api_key, model="gemini-flash-lite-latest"):
    from google import genai
    client = genai.Client(api_key=api_key)
    ultimo_error = None
    for modelo in (model, _RESPALDO_GEMINI):
        try:
            response = client.models.generate_content(model=modelo, contents=prompt)
            return response.text.strip().replace('"', "")
        except Exception as e:
            ultimo_error = e
    raise ultimo_error


def chat_completion(base_url, model, api_key, system_prompt, user_content, max_tokens):
    from openai import OpenAI
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip().replace('"', "")
