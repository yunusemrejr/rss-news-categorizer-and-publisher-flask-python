from flask import Flask, request, jsonify
from xml.etree import ElementTree as ET
import logging
import requests
import json
import os

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

HISTORY_FILE = 'history.json'
MAX_HISTORY_SIZE = 1000

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            app.logger.debug('Failed to load history: JSONDecodeError. Initializing empty history.')
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def check_and_reset_history():
    history = load_history()
    if len(history) > MAX_HISTORY_SIZE:
        app.logger.debug('History size exceeded limit. Resetting history.')
        history = []
        save_history(history)
    return history

@app.route('/')
def home():
    return "This is a blank page. Please go back home :)"

@app.route('/input', methods=['POST'])
def input():
    if request.content_type != 'application/xml':
        app.logger.debug('Invalid content type')
        return jsonify({'message': 'Invalid content type'}), 400

    xml_data = request.data.decode('utf-8')
    if not xml_data:
        app.logger.debug('No data received')
        return jsonify({'message': 'No data received'}), 400

    app.logger.debug('Received XML data: %s', xml_data)
    
    try:
        root = ET.fromstring(xml_data)
        if root.tag != 'news' or not all(root.findall('article')):
            app.logger.debug('Invalid XML format: root tag or articles missing')
            return jsonify({'message': 'Invalid XML format'}), 400
        
        news_data = {}
        history = check_and_reset_history()
        new_articles = {}
        
        for article in root.findall('article'):
            title = article.find('title').text if article.find('title') is not None else None
            text = article.find('text').text if article.find('text') is not None else None
            if not text:
                text = article.find('body').text if article.find('body') is not None else None
            url = article.find('link').text if article.find('link') is not None else "N/A"
            date = article.find('date').text if article.find('date') is not None else None
            image_element = article.find('image')
            image = image_element.text if image_element is not None else None
            
            app.logger.debug('Article - Title: %s, Text: %s, URL: %s, Date: %s, Image: %s',
                             title, text, url, date, image)
            
            if not all([title, text, date]) or title in history:
                app.logger.debug('Invalid XML: Missing required fields in article or already processed')
                continue  # Skip this article if it doesn't have the required fields or is already processed
            
            news_data[title] = {
                'text': text,
                'url': url,
                'date': date,
                'image': image
            }
            new_articles[title] = news_data[title]
            history.append(title)
        
        if new_articles:
            save_history(history)
            ai_endpoint = 'http://localhost:5001/analyze'
            response = requests.post(ai_endpoint, json={'articles': new_articles})
            app.logger.debug('Response from AI: %s', response.status_code)
            return jsonify({'message': 'Articles accepted', 'data': new_articles}), 200
        else:
            app.logger.debug('No new articles to process')
            return jsonify({'message': 'Waiting for new news'}), 200
        
    except ET.ParseError as e:
        app.logger.debug('XML parsing error: %s', str(e))
        return jsonify({'message': 'Invalid XML format'}), 400

@app.route('/output', methods=['POST'])
def output():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(debug=True)
