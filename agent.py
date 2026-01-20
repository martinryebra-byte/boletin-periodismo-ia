import os
import requests
from newspaper import Article
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ==============================
# CONFIGURACIÓN
# ==============================
TEST_MODE = False
MAX_ARTICLES = 5
HISTORIAL_FILE = "boletin_historial.txt"

MEDIOS = {
    # España / Argentina
    "El País": "https://elpais.com/rss/",
    "La Nación": "https://www.lanacion.com.ar/rss/nota.xml",
    "El Mundo": "https://www.elmundo.es/rss/espana.xml",

    # Inglés
    "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "Wall Street Journal": "https://www.wsj.com/xml/rss/3_7014.xml",
    "Financial Times": "https://www.ft.com/?format=rss",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "The Times of London": "https://www.thetimes.co.uk/rss",

    # Francés
    "Le Monde": "https://www.lemonde.fr/rss/une.xml",

    # Alternativos / digitales
    "Axios": "https://www.axios.com/feed",
    "Vox": "https://www.vox.com/rss/index.xml",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Politico": "https://www.politico.com/rss/politicopicks.xml",
    "BuzzFeed News": "https://www.buzzfeed.com/world.xml",

    # Escandinavos
    "Dagens Nyheter (Suecia)": "https://www.dn.se/m/rss/",
    "Aftenposten (Noruega)": "https://www.aftenposten.no/rss",
    "Politiken (Dinamarca)": "https://politiken.dk/rss/nyheder",
    "Berlingske (Dinamarca)": "https://www.berlingske.dk/rss",

    # Italiano
    "Corriere della Sera": "https://www.corriere.it/rss/homepage.xml",
}

# Correo
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
        print(f"Error RSS {rss_url}: {e}")
        return []

def descargar_articulo(url):
    try:
        art = Article(url)
        art.download()
        art.parse()
        return {"title": art.title, "text": art.text[:1500], "url": url}
    except Exception as e:
        return {"title": "ERROR", "text": str(e), "url": url}

def es_posible_ia(texto):
    # Método simple: busca palabras clave que sugieran IA (puede mejorar con regex)
    keywords = ["AI", "artificial intelligence", "generado por IA", "machine learning"]
    return any(k.lower() in texto.lower() for k in keywords)

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

def guardar_historial(texto):
    try:
        with open(HISTORIAL_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write(texto)
    except Exception as e:
        print("Error al guardar historial:", e)

# ==============================
# MAIN
# ==============================
boletin = []
urls_vistos = set()

# Configurar OpenAI
if not TEST_MODE:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No hay API Key definida. Cambiando a TEST_MODE.")
        TEST_MODE = True
    else:
        client = OpenAI(api_key=api_key)

# Procesar cada medio
for medio, rss_url in MEDIOS.items():
    urls = obtener_urls_rss(rss_url, MAX_ARTICLES)
    for url in urls:
        if url in urls_vistos:
            continue  # Evita duplicados
        urls_vistos.add(url)

        art = descargar_articulo(url)
        ia_detectada = es_posible_ia(art["text"])

        if TEST_MODE:
            resumen = f"(Modo prueba) {medio} - {art['title']}\nExtracto: {art['text']}\nPosible IA: {ia_detectada}"
        else:
            resumen = resumir_articulo(client, art["text"])
            if ia_detectada:
                resumen = "(Posible contenido asistido por IA)\n" + resumen

        boletin.append(f"{medio} - {art['title']}\n{resumen}\n{art['url']}\n{'-'*50}")

# Crear boletín final
boletin_texto = "\n\n".join(boletin)
print("=== Boletín diario ===")
print(boletin_texto)

# Guardar histórico
guardar_historial(boletin_texto)

# Enviar correo
if SMTP_USER and SMTP_PASS:
    enviar_correo("Boletín diario de noticias IA", boletin_texto)
