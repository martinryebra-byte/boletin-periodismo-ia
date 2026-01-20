import os
from newspaper import Article
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText

# ==============================
# CONFIGURACIÓN
# ==============================
TEST_MODE = False  # Cambia a True si quieres probar sin gastar crédito

# Lista de URLs de medios (puedes agregar más)
urls = [
    "https://elpais.com",
    "https://www.nytimes.com",
    "https://www.lanacion.com.ar",
]

# Datos para correo (si quieres enviar el boletín)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("EMAIL_USER")   # define esto como secreto en GitHub
SMTP_PASS = os.getenv("EMAIL_PASS")   # define esto como secreto en GitHub
TO_EMAIL = os.getenv("TO_EMAIL", SMTP_USER)

# ==============================
# FUNCIONES
# ==============================
def descargar_articulo(url):
    try:
        art = Article(url)
        art.download()
        art.parse()
        return {"title": art.title, "text": art.text[:500], "url": url}
    except Exception as e:
        return {"title": "ERROR", "text": str(e), "url": url}

def resumir_articulo(client, texto):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Resume este texto en español:\n\n{texto}"}],
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

# Si estamos en modo prueba, no usamos OpenAI
if not TEST_MODE:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No hay API Key definida. Cambiando a TEST_MODE para no usar OpenAI.")
        TEST_MODE = True
    else:
        client = OpenAI(api_key=api_key)

# Procesar cada URL
for url in urls:
    art = descargar_articulo(url)
    if TEST_MODE:
        resumen = f"(Modo prueba) Título: {art['title']}\nExtracto: {art['text']}"
    else:
        resumen = resumir_articulo(client, art["text"])
    boletin.append(f"{art['title']}\n{resumen}\n{art['url']}\n{'-'*50}")

# Crear boletín final
boletin_texto = "\n\n".join(boletin)
print("=== Boletín diario ===")
print(boletin_texto)

# Enviar correo si están configurados SMTP_USER y SMTP_PASS
if SMTP_USER and SMTP_PASS:
    enviar_correo("Boletín diario de noticias IA", boletin_texto)
