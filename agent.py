import os
import requests
from newspaper import Article
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText

# ==============================
# CONFIGURACIÓN
# ==============================
TEST_MODE = False          # True = modo prueba, no usa OpenAI
MAX_ARTICLES = 5           # Número máximo de artículos por medio

# Lista de medios influyentes y alternativos con RSS
MEDIOS = {
    # Medios en español
    "El País": "https://elpais.com/rss/",
    "La Nación": "https://www.lanacion.com.ar/rss/nota.xml",
    "El Mundo": "https://www.elmundo.es/rss/espana.xml",

    # Medios en inglés
    "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "Wall Street Journal": "https://www.wsj.com/xml/rss/3_7014.xml",
    "Financial Times": "https://www.ft.com/?format=rss",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "The Times of London": "https://www.thetimes.co.uk/rss",

    # Medios en francés
    "Le Monde": "https://www.lemonde.fr/rss/une.xml",

    # Medios alternativos / digitales
    "Axios": "https://www.axios.com/feed",
    "Vox": "https://www.vox.com/rss/index.xml",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Politico": "https://www.politico.com/rss/politicopicks.xml",
    "BuzzFeed News": "https://www.buzzfeed.com/world.xml",

    # Medios escandinavos innovadores
    "Dagens Nyheter (Suecia)": "https://www.dn.se/m/rss/",
    "Aftenposten (Noruega)": "https://www.aftenposten.no/rss",
    "Politiken (Dinamarca)": "https://politiken.dk/rss/nyheder",
    "Berlingske (Dinamarca)": "https://www.berlingske.dk/rss",
}

# Datos para correo
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("EMAIL_USER")
SMTP_PASS = os.getenv("EMAIL_PASS")
TO_EMAIL = os.getenv("TO_EMAIL", SMTP_USER)

# ==============================
# FUNCIONES
# ==============================
def obtener_urls_rss(rss_url, max_articles=5):
    try:
        resp = requests.get(rss_url, timeout=10)
        if resp.status_code != 200:
            return []
        from xml.etree import ElementTree as ET
        root = ET.fromstring(resp.content)
        urls = [item.find("link").text for item in root.findall(".//item") if item.find("link") is not None]
        return urls[:max_articles]
    except Exception as e:
        print(f"Error al obtener RSS {rss_url}: {e}")
        return []

def descargar_articulo(url):
    try:
        art = Article(url)
        art.download()
        art.parse()
        return {"title": art.title, "text": art.text[:1000], "url": url}
    except Exception as e:
        return {"title": "ERROR", "text": str(e), "url": url}

def resumir_articulo(client, texto):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Resume este texto en español y marca si parece contenido generado por IA:\n\n{texto}"}],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"(Error al generar resumen: {e})"

def enviar_correo(asunto, cuerpo):
    try:
        msg = MIMEText(cuerpo, "plain", "utf-8")
        msg["Subject"] = asunto
        msg["From"] = SMTP_USER
        msg["To"] = TO_EMAIL
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print("Correo enviado correctamente a", TO_EMAIL)
    except Exception as e:
        print("Error al enviar correo:", e)

# ==============================
# MAIN
# ==============================
boletin = []

# Configurar OpenAI
if not TEST_MODE:
    api_k_
