from flask import Flask, request, jsonify, Response
import logging
from transformers import pipeline
import xml.etree.ElementTree as ET

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Initialize the Hugging Face sentiment analysis pipeline
classifier = pipeline("sentiment-analysis")

categorized_articles = []

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    if not data or 'articles' not in data:
        app.logger.error('No data received or incorrect format')
        return jsonify({'message': 'No data received or incorrect format'}), 400
    
    articles = data['articles']
    new_categorized_articles = []
    
    for title, details in articles.items():
        content = details.get('text', '')
        combined_text = title + " " + content[:500]
        result = classifier(combined_text[:512])  # BERT model max token limit 512
        
        # Map sentiment to categories
        category = "breaking" if result[0]['label'] == 'POSITIVE' else "alerting"
        
        article_data = {
            'title': title,
            'category': category,
            'text': details['text'],
            'url': details['url'],
            'date': details['date'],
            'image': details['image']
        }
        new_categorized_articles.append(article_data)
        app.logger.debug('Article passed verification: %s', title)
    
    global categorized_articles
    categorized_articles.extend(new_categorized_articles)
    
    for article in new_categorized_articles:
        print(f"Title: {article['title']}\nCategory: {article['category']}\nDate: {article['date']}\nURL: {article['url']}\nImage: {article['image']}\nText: {article['text'][:500]}\n\n")
    
    return jsonify({'message': 'Analysis complete', 'categorized_articles': new_categorized_articles}), 200

@app.route('/feed', methods=['GET'])
def feed():
    root = ET.Element('articles')
    
    for article in categorized_articles:
        article_element = ET.SubElement(root, 'article')
        
        title_element = ET.SubElement(article_element, 'title')
        title_element.text = article['title']
        
        category_element = ET.SubElement(article_element, 'category')
        category_element.text = article['category']
        
        date_element = ET.SubElement(article_element, 'date')
        date_element.text = article['date']
        
        text_element = ET.SubElement(article_element, 'text')
        text_element.text = article['text']
        
        url_element = ET.SubElement(article_element, 'url')
        url_element.text = article['url']
        
        if article['image']:
            image_element = ET.SubElement(article_element, 'image')
            image_element.text = article['image']
    
    xml_data = ET.tostring(root, encoding='utf-8')
    return Response(xml_data, mimetype='application/xml')

if __name__ == '__main__':
    app.run(port=5001, debug=True)
