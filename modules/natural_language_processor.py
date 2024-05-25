# modules/natural_language_processor.py

from bs4 import BeautifulSoup
import spacy
from nltk import pos_tag
from nltk.tokenize import word_tokenize
import re

class NaturalLanguageProcessor:
    def __init__(self):
        # Initialize necessary NLP models and tools
        self.nlp = spacy.load('en_core_web_sm')

    def clean_html(self, html_content):
        # Use BeautifulSoup to remove HTML tags
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):  # remove all javascript and stylesheet code
            script.extract()
        return soup.get_text()


    def process_text(self, text, engine='spacy'):
        # Process the extracted text using NLP techniques
        if engine == 'spacy':
            doc = self.nlp(text)
            pos_tags = [(token.text, token.pos_) for token in doc]
            return pos_tags
        tokens = word_tokenize(text)
        pos_tags = pos_tag(tokens)
        return pos_tags

    def find_element(self, element_name, doc):
        for ent in doc.ents:
            if ent.label_ == element_name:
                return ent.text
        return None

    def get_element_code(self, soup, element):
        # Return the source code of the found HTML element
        element = soup.find(element)
        return str(element) if element else None

    def extract_relevant_text(self, soup_object, element_name):
        text = soup_object.get_text()
        if element_name == 'price':
            return re.findall(r'\d+\.\d+', text)
        return text

    def get_element_value(self, soup, element):
        element_code = str(soup.find(element))
        return re.findall(r'\d+\.\d+', element_code)
