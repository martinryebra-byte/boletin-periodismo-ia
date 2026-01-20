import feedparser
import sqlite3
import os
import smtplib
from email.mime.text import MIMEText
from newspaper import Article
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime, timedelta

from sources import RSS_FEEDS
from prompts import CLASSIFICATION_PROMPT, SUMMARY_PROMPT

load_dotenv()
client = OpenAI()

DB = "db.sqlite"
RECIPIENT = "myebra@lanacion.com.ar"

# ------------------ DB ------------------

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            url TEXT PRIMARY KEY,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

def seen(url):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
    result = c.fetchone()
    conn.close()
    return result is not None

def mark_seen(url):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO articles VALUES (?, ?)", 
              (url, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

# ------------------ IA ------------------

def ask_llm(prompt, text):
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text[:12000]}
        ],
        temperature=0
    )
    return response.choices[0].message.content

# ------------------ EMAIL ------------------

def send_email(html):
    msg = MIMEText(html, "html")
    msg["Subject"] = f"🗞️ Periodismo e IA – {datetime.now().strftime('%d/%m/%Y')}"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = RECIPIENT

    with smtplib.SMTP(os.environ["SMTP_SERVER"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.send_message(msg)

# ------------------ MAIN ------------------

def run():
    init_db()
    confirmed = []

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            url = entry.link
            if seen(url):
                continue

            try:
                art = Article(url)
                art.download()
                art.parse()
                text = art.text
            except:
                continue

            classification = ask_llm(CLASSIFICATION_PROMPT, text)

            if '"CONFIRMADO"' in classification:
                summary = ask_llm(SUMMARY_PROMPT, text)
                confirmed.append({
                    "title": art.title,
                    "source": feed.feed.get("title", ""),
                    "summary": summary,
                    "url": url
                })

            mark_seen(url)

    if not confirmed:
        return

    html = ""
    for a in confirmed[:10]:
        html += f"""
        <h3>📰 {a['source']}</h3>
        <b>{a['title']}</b>
        <p>{a['summary']}</p>
        <a href="{a['url']}">Leer artículo</a>
        <hr>
        """

    send_email(html)

if __name__ == "__main__":
    run()
