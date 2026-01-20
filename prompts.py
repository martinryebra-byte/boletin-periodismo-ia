CLASSIFICATION_PROMPT = """
Eres un editor senior especializado en periodismo e inteligencia artificial.

Evalúa el siguiente artículo y responde SOLO en JSON válido.

Criterio:
El artículo se considera CONFIRMADO únicamente si existe evidencia explícita
de participación de IA en su elaboración periodística (redacción, edición,
análisis de datos, visuales, automatización editorial) O si es una investigación
documentada sobre uso de IA en periodismo.

Responde con:
{
  "veredicto": "CONFIRMADO" | "DESCARTADO",
  "justificacion": "breve explicación"
}
"""

SUMMARY_PROMPT = """
Resume el siguiente artículo en español, en 2 a 4 líneas,
con tono de boletín editorial profesional.
"""
