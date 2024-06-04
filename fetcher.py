import requests
import xml.etree.ElementTree as ET
import time

rss_feeds = [
    'http://feeds.bbci.co.uk/news/rss.xml',
    'http://rss.cnn.com/rss/edition.rss',
    'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
    'https://feeds.a.dj.com/rss/RSSWorldNews.xml',
    'https://www.aljazeera.com/xml/rss/all.xml',
    'https://www.reuters.com/tools/rss',
    'https://feeds.npr.org/1001/rss.xml',
    'https://www.theguardian.com/world/rss',
    'https://www.ft.com/?format=rss',
    'https://www.economist.com/latest/rss.xml',
    'https://www.bloomberg.com/feed/podcast/have-a-nice-future.xml',
    'https://rss.dw.com/rdf/rss-en-all',
    'https://www.sciencedaily.com/rss/all.xml',
    'https://www.nationalgeographic.com/content/natgeo/en_us/rss/index.rss',
    'https://www.techradar.com/rss',
    'https://feeds.feedburner.com/TechCrunch/',
    'https://www.wired.com/feed/rss',
    'https://www.vice.com/en_us/rss',
    'https://www.politico.com/rss/politics08.xml',
    'https://rss.politico.com/politics-news.xml',
    'https://feeds.bloomberg.com/bview/news.rss',
    'https://www.yahoo.com/news/rss',
    'https://abcnews.go.com/abcnews/topstories',
]


def alternative_tag_syntax(xml_payload):
    possible_tags = {
        'title': ['head', 'summary', 'postTitle', 'title'],
        'text': ['details', 'postBody', 'content', 'description', 'body'],
        'date': ['date', 'published', 'pubDate', 'postDate']
    }

    new_tags = {}
    for key, tags in possible_tags.items():
        for tag in tags:
            if xml_payload[0].find(tag) is not None:
                new_tags[key] = tag
                break

    return new_tags

def rss_get(feed_url):
    try:
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch feed at {feed_url}: {e}")
        return []

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        print(f"Failed to parse XML from {feed_url}: {e}")
        return []

    articles = []

    for item in root.findall('./channel/item')[:5]:
        title = item.find('title').text if item.find('title') is not None else ''
        text = item.find('description').text if item.find('description') is not None else ''
        date = item.find('pubDate').text if item.find('pubDate') is not None else ''
        url = item.find('link').text if item.find('link') is not None else ''

        if not all([title, text, date, url]):
            new_tags = alternative_tag_syntax(root.findall('./channel/item')[:1])
            title = item.find(new_tags.get('title', '')).text if item.find(new_tags.get('title', '')) is not None else ''
            text = item.find(new_tags.get('text', '')).text if item.find(new_tags.get('text', '')) is not None else ''
            date = item.find(new_tags.get('date', '')).text if item.find(new_tags.get('date', '')) is not None else ''
            url = item.find('link').text if item.find('link') is not None else ''

        image = None
        media_content = item.find('media:content')
        if media_content is not None:
            image = media_content.attrib.get('url')
        else:
            media_thumbnail = item.find('media:thumbnail')
            if media_thumbnail is not None:
                image = media_thumbnail.attrib.get('url')

        article = {
            'title': title,
            'date': date,
            'text': text,
            'url': url,
            'image': image
        }

        articles.append(article)

    return articles

def fetch_and_send():
    all_articles = []
    for feed in rss_feeds:
        articles = rss_get(feed)
        all_articles.extend(articles)

    news = ET.Element('news')
    for article in all_articles:
        article_element = ET.SubElement(news, 'article')
        for key, value in article.items():
            sub_element = ET.SubElement(article_element, key)
            if value:
                sub_element.text = value

    xml_data = ET.tostring(news, encoding='utf-8')
    print(f"XML Data: {xml_data.decode('utf-8')}")

    endpoint_url = 'http://localhost:5000/input'
    headers = {'Content-Type': 'application/xml'}
    try:
        response = requests.post(endpoint_url, data=xml_data, headers=headers)
        print(f'Response: {response.status_code}')
    except requests.RequestException as e:
        print(f"Failed to send data: {e}")

if __name__ == "__main__":
    while True:
        fetch_and_send()
        time.sleep(600)  # Fetch and send every 10 minutes
