from flask import Flask, render_template, jsonify
import json
import random
import requests
import re
import os

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'wiki_articles.json')


def load_articles():
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_wikipedia_text(title: str, lang: str = 'en') -> str:
    api_url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        'action': 'query',
        'titles': title,
        'prop': 'extracts',
        'explaintext': True,
        'exsectionformat': 'plain',
        'format': 'json',
    }
    try:
        resp = requests.get(api_url, params=params, timeout=10)
        data = resp.json()
        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            extract = page.get('extract', '')
            if extract:
                return extract
    except Exception as e:
        print(f"Error fetching Wikipedia article '{title}': {e}")
    return ''


def extract_paragraphs(text: str, count: int = 4) -> str:
    """Extract 4-5 meaningful paragraphs from article text."""
    # Split on double newlines, filter empty and section headers
    raw_paras = re.split(r'\n{2,}', text)
    paras = []
    for p in raw_paras:
        p = p.strip()
        # Skip section headers (short lines, no spaces typically) and very short paragraphs
        if len(p) < 80:
            continue
        # Skip lines that look like headers (no periods, short)
        if '\n' not in p and len(p) < 120 and '.' not in p:
            continue
        paras.append(p)
        if len(paras) >= count:
            break

    if not paras:
        return text[:2000]  # fallback

    return '\n\n'.join(paras)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/text')
def get_text():
    db = load_articles()
    articles = db.get('articles', [])
    if not articles:
        return jsonify({'error': 'No articles in database'}), 500

    article = random.choice(articles)
    raw_text = get_wikipedia_text(article['title'], article.get('lang', 'en'))

    if not raw_text:
        return jsonify({'error': 'Could not fetch article'}), 503

    paragraphs = extract_paragraphs(raw_text, count=random.randint(4, 5))

    return jsonify({
        'text': paragraphs,
        'source': article['title'],
        'url': article['url'],
        'category': article.get('category', '')
    })


if __name__ == '__main__':
    app.run(debug=True)
