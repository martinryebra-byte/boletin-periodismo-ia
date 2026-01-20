import os
from openai import OpenAI

# Obtener la API Key desde la variable de entorno
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY no está definida. Configura el secreto en GitHub.")

client = OpenAI(api_key=api_key)

# Prueba mínima: generar un texto corto
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Escribe una frase corta de prueba en español."}],
    temperature=0.3
)

print("Respuesta de OpenAI:", response.choices[0].message.content)
