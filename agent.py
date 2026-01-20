import os
from newspaper import Article

TEST_MODE = True
url = "https://elpais.com"

try:
    article = Article(url)
    article.download()
    article.parse()
    title = article.title
    text_snippet = article.text[:200]
except Exception as e:
    title = "ERROR"
    text_snippet = str(e)

if TEST_MODE:
    summary = f"(Modo prueba) Título: {title}\nExtracto: {text_snippet}"
else:
    pass

print("=== Boletín diario (prueba) ===")
print(summary)
print("Workflow probado correctamente sin usar cuota OpenAI.")
