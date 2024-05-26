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


# --- Data Cleansing Functions ---
nlp = spacy.load('en_core_web_sm')

def clean_laptop_data(data: list[dict]) -> list[dict]:
    """Cleans the scraped laptop data using rule-based and ML approaches.

    Args:
        data: A list of dictionaries where each dictionary represents a laptop.

    Returns:
        A list of dictionaries with cleaned data.
    """

    cleaned_data = []
    for laptop in data:
        cleaned_laptop = {}
        for key, value in laptop.items():
            if key == 'Price':
                cleaned_laptop[key] = clean_price(value)
            elif key == 'Shipping Cost':
                cleaned_laptop[key] = clean_shipping_cost(value)
            elif key == 'Time Left':
                cleaned_laptop[key] = clean_time_left(value)
            elif key == 'Name':
                cleaned_laptop[key] = clean_laptop_name_spacy(value)  # Use spaCy cleaning
            # ... (add cleaning for other fields as needed)
            else:
                cleaned_laptop[key] = value
        cleaned_data.append(cleaned_laptop)
    return cleaned_data

def clean_price(price: str) -> float:
    """Removes currency symbols, commas, and converts to float."""
    if isinstance(price, str):
        price = price.replace('$', '').replace(',', '').replace(' ', '').strip()
        try:
            return float(price)
        except ValueError:
            return "N/A"  # Or handle the error differently
    else:
        return price  # Already in a numeric format

def clean_shipping_cost(shipping_cost: str) -> float:
    """Standardizes free shipping, removes symbols, and converts to float."""
    if isinstance(shipping_cost, str):
        if 'free' in shipping_cost.lower() or 'бесплатная' in shipping_cost.lower():  # check in both languages
            return 0.0
        else:
            shipping_cost = shipping_cost.replace('$', '').replace(',', '').strip()
            try:
                return float(shipping_cost)
            except ValueError:
                return "N/A"
    else:
        return shipping_cost

def clean_time_left(time_left: str) -> str:
    """Cleans the 'Time Left' field (not implemented yet)."""
    # TODO: Implement your logic to extract numeric components (days, hours)
    # and convert to a consistent unit, e.g., total hours remaining.
    return time_left

def clean_laptop_name_spacy(laptop_name: str) -> str:
    """Cleans laptop names using spaCy for basic entity recognition.

    Args:
        laptop_name: The raw laptop name extracted from eBay.

    Returns:
        A cleaned laptop name.
    """
    doc = nlp(laptop_name)
    cleaned_name = []
    for token in doc:
        # Basic cleanup:
        if token.pos_ in ('PROPN', 'NUM', 'NOUN', 'ADJ'):  # Keep important word types
            cleaned_name.append(token.text)

    return " ".join(cleaned_name) if cleaned_name else "N/A"

# --- Example Usage (You'll call this after scraping) ---
raw_laptop_data = [
    # ... (your scraped data in a list of dictionaries)
]

cleaned_laptop_data = clean_laptop_data(raw_laptop_data)

# --- Now you can use the cleaned_laptop_data for your analysis or saving to Google Sheets ---