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
    headers = {
        'User-Agent': 'ColabNotebook/1.0 (https://colab.research.google.com; user@example.com)'
    }
    try:
        resp = requests.get(api_url, params=params, headers=headers, timeout=10)

        print(f"Wikipedia API Response Status Code for '{title}': {resp.status_code}")
        if resp.status_code != 200:
            print(f" Код ответа API Википедии для '{title}': {resp.text[:120]}...")
            return ''

        data = resp.json()
        pages = data.get('query', {}).get('pages', {})
        for page in pages.values():
            extract = page.get('extract', '')
            if extract:
                return extract
    except Exception as e:
        print(f"Ошибка при загрузке статьи '{title}': {e}")
    return ''


def extract_paragraphs(text: str, count: int = 4) -> str:
    raw_paras = re.split(r'\n{2,}', text)
    paras = []
    for p in raw_paras:
        p = p.strip()
        if len(p) < 20:
            continue
        if '\n' not in p and len(p) < 120 and '.' not in p:
            continue
        paras.append(p)
        if len(paras) >= count:
            break

    if not paras:
        return text[:120]

    return '\n\n'.join(paras)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/text')
def get_text():
    db = load_articles()
    articles = db.get('articles', [])
    if not articles:
        return jsonify({'error': 'В базе данных отсутствуют статьи'}), 200

    article = random.choice(articles)
    raw_text = get_wikipedia_text(article['title'], article.get('lang', 'en'))

    if not raw_text:
        return jsonify({'error': 'Статья не найдена'}), 503

    paragraphs = extract_paragraphs(raw_text, count=random.randint(1, 2))

    return jsonify({
        'text': paragraphs,
        'source': article['title'],
        'url': article['url'],
        'category': article.get('category', '')
    })


if __name__ == '__main__':
    app.run(debug=True)
