import os
import requests
from newspaper import Article
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText

# ==============================
# CONFIGURACIÓN
# ==============================
TEST_MODE = False  # True = modo prueba, no usa OpenAI
MAX_ARTICLES = 5   # Número máximo de artículos por medio

# Lista de medios a monitorear
MEDIOS = {
    "El País": "https://elpais.com/rss/",
    "NYT": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "La Nación": "https://www.lanacion.com.ar/rss/nota.xml",
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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No hay API Key definida. Cambiando a TEST_MODE para no usar OpenAI.")
        TEST_MODE = True
    else:
        client = OpenAI(api_key=api_key)

# Recorrer medios
for medio, rss_url in MEDIOS.items():
    urls = obtener_urls_rss(rss_url, MAX_ARTICLES)
    for url in urls:
        art = descargar_articulo(url)
        if TEST_MODE:
            resumen = f"(Modo prueba) {medio} - {art['title']}\nExtracto: {art['text']}"
        else:
            resumen = resumir_articulo(client, art["text"])
        boletin.append(f"{medio} - {art['title']}\n{resumen}\n{art['url']}\n{'-'*50}")

# Generar boletín final
boletin_texto = "\n\n".join(boletin)
print("=== Boletín diario ===")
print(boletin_texto)

# Enviar correo si están configurados SMTP_USER y SMTP_PASS
if SMTP_USER and SMTP_PASS:
    enviar_correo("Boletín diario de noticias IA", boletin_texto)
