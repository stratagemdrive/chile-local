import feedparser
import json
import os
from datetime import datetime, timedelta
from googletrans import Translator
from dateutil import parser as date_parser

# Configuration
COUNTRY = "chile"
RSS_FEEDS = {
    "The Clinic": "https://www.theclinic.cl/feed/",
    "La Tercera": "https://www.latercera.com/arc/outboundfeeds/rss/",
    "El Mostrador": "https://www.elmostrador.cl/feed/",
    "Diario Financiero": "https://www.df.cl/noticias/site/tax/port/all/rss_2_0.xml",
    "El Dinamo": "https://www.eldinamo.cl/feed/",
    "El Desconcierto": "https://www.eldesconcierto.cl/feed/",
    "Cooperativa": "https://www.cooperativa.cl/noticias/site/tax/port/all/rss_2_0.xml"
}

CATEGORIES = ["Diplomacy", "Military", "Energy", "Economy", "Local Events"]
MAX_AGE_DAYS = 7
TARGET_PER_CAT = 20
FILE_PATH = f"docs/{COUNTRY}_news.json"

translator = Translator()

def get_category(text):
    text = text.lower()
    if any(word in text for word in ['diplomacia', 'canciller', 'embajador', 'relaciones']): return "Diplomacy"
    if any(word in text for word in ['militar', 'ejército', 'armada', 'fuerzas armadas']): return "Military"
    if any(word in text for word in ['energía', 'eléctrica', 'litio', 'solar', 'combustible']): return "Energy"
    if any(word in text for word in ['economía', 'pib', 'mercado', 'banco', 'hacienda']): return "Economy"
    return "Local Events"

def fetch_and_process():
    if not os.path.exists("docs"):
        os.makedirs("docs")

    existing_data = []
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'r') as f:
            existing_data = json.load(f)

    new_stories = []
    seen_urls = {s['url'] for s in existing_data}
    now = datetime.now(datetime.now().astimezone().tzinfo)

    for source_name, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            try:
                pub_date = date_parser.parse(entry.published)
                if now - pub_date > timedelta(days=MAX_AGE_DAYS):
                    continue
                
                if entry.link not in seen_urls:
                    # Translate Title (Spanish to English)
                    translated_title = translator.translate(entry.title, src='es', dest='en').text
                    
                    story = {
                        "title": translated_title,
                        "source": source_name,
                        "url": entry.link,
                        "published_date": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "category": get_category(entry.title + " " + getattr(entry, 'summary', ''))
                    }
                    new_stories.append(story)
                    seen_urls.add(entry.link)
            except Exception:
                continue

    # Merge and filter
    combined = new_stories + existing_data
    # Remove duplicates and items > 7 days
    final_list = []
    seen = set()
    for s in combined:
        dt = datetime.strptime(s['published_date'], "%Y-%m-%d %H:%M:%S")
        if dt > (datetime.now() - timedelta(days=MAX_AGE_DAYS)) and s['url'] not in seen:
            final_list.append(s)
            seen.add(s['url'])

    # Sort by date descending
    final_list.sort(key=lambda x: x['published_date'], reverse=True)

    # Group and limit to 20 per category
    categorized_output = []
    for cat in CATEGORIES:
        cat_stories = [s for s in final_list if s['category'] == cat][:TARGET_PER_CAT]
        categorized_output.extend(cat_stories)

    with open(FILE_PATH, 'w') as f:
        json.dump(categorized_output, f, indent=4)

if __name__ == "__main__":
    fetch_and_process()
