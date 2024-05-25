# modules/natural_language_processor.py

from bs4 import BeautifulSoup
import spacy
from nltk import pos_tag
from nltk.tokenize import word_tokenize
import re

class NaturalLanguageProcessor:
    def __init__(self):
        # Initialize necessary NLP models and tools
        self.pos_tagger = pos_tag
        self.nlp = spacy.load('en_core_web_sm')

    def parse_html(self, html_content):
        # Parse the HTML content and return a BeautifulSoup object
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup

    def extract_text(self, soup_object):
        # Extract all text from the parsed HTML content
        text = soup_object.get_text()
        return text

    def process_text(self, text, engine='spacy'):
        # Process the extracted text using NLP techniques
        if engine == 'spacy':
            doc = self.nlp(text)
            pos_tags = [(token.text, token.pos_) for token in doc]
            return pos_tags
        tokens = word_tokenize(text)
        pos_tags = self.pos_tagger(tokens)
        return pos_tags

    def find_element(self, element_name, tokens):
        # Find the HTML element that corresponds to the given element name
        if element_name in tokens:
            return element_name
        else:
            return None

    def get_element_code(self, soup, element):
        # Return the source code of the found HTML element
        element_code = str(soup.find(element))
        return element_code
