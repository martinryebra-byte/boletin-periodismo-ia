import os
import feedparser
from newspaper import Article
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText

# ==============================
# 1️⃣ Configuración de la API Key
# ==============================
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY no está definida. Configura el secreto en GitHub.")
client = OpenAI(api_key=api_key)

# ==============================
# 2️⃣ Configuración del correo
# ==============================
SMTP_HOST = "smtp.tu-servidor.com"  # Cambia por tu servidor SMTP
SMTP_PORT = 587
SMTP_USER = "myebra@lanacion.com.ar"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Puedes guardar la contraseña como secreto en GitHub

TO_EMAIL = "myebra@lanacion.com.ar"

# ==============================
# 3️⃣ Lista de fuentes
# ==============================
sources = [
    "https://www.nytimes.com/rss",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "https://elpais.com/rss/feed.html",
    "https://www.lanacion.com.ar/rss",
    "https://www.lemonde.fr/rss/",
    # Puedes agregar más
]

# ==============================
# 4️⃣ Funciones
# ==============================
def fetch_articles():
    articles = []
    for feed_url in sources:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:  # Solo los 3 primeros artículos por fuente
            articles.append(entry.link)
    return articles

def summarize_article(url):
    article = Article(url)
    article.download()
    article.parse()
    text = article.text
    # Llamada a OpenAI para resumir en español
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Resume en español: {text}"}],
        temperature=0.3,
    )
    summary = response.choices[0].message.content
    return summary

def send_email(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

# ==============================
# 5️⃣ Generar boletín
# ==============================
def main():
    articles = fetch_articles()
    boletin = ""
    for url in articles:
        try:
            summary = summarize_article(url)
            boletin += f"{url}\n{summary}\n\n"
        except Exception as e:
            boletin += f"{url}\nERROR: {e}\n\n"

    send_email("Boletín diario de artículos IA", boletin)
    print("Boletín enviado correctamente.")

if __name__ == "__main__":
    main()
