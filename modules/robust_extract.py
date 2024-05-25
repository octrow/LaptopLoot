import spacy
from loguru import logger
from spacy.matcher import Matcher
from bs4 import BeautifulSoup
import re
import logging

# Configure logging (using Loguru)
logger.add("laptoploot_extraction.log", level="INFO", format="{time} - {level} - {message}")

nlp = spacy.load("en_core_web_sm")

# --- Helper Functions ---
def _extract_price_from_text(text):
    """Extracts price from a string using regex."""
    price_match = re.search(r'(?:US\s\$|C\s\$|£|€|A\s\$|\$)\s*\d+(?:,\d{3})*(?:\.\d{2})?', text)
    if price_match:
        try:
            # More robust handling of different currency symbols and spacing
            price = float(price_match.group(0).replace(',', '').replace('$', '').replace('US', '').replace('C', '').replace('A', '').strip())
            return price
        except ValueError as e:
            logger.error(f"Error converting price text to float: {e}, Text: {price_match.group(0)}")
            return None
    return None

def _extract_price_from_spacy_doc(doc, window_size=5):
    """Finds price-related entities and analyzes surrounding tokens."""
    price_keywords = ['price', 'cost', 'selling', 'buy', 'now', 'for', 'was', 'to']
    price_matcher = Matcher(nlp.vocab)

    # Create flexible patterns to match different price formats
    price_patterns = [
        [{"LIKE_NUM": True, "OP": "?"}, {"ORTH": "$"}, {"LIKE_NUM": True}],
        [{"ORTH": "$"}, {"LIKE_NUM": True}],
        [{"TEXT": {"REGEX": r"(?:US\s\$|C\s\$|£|€|A\s\$)"}}, {"LIKE_NUM": True}],
        # Add more patterns as needed
    ]

    for pattern in price_patterns:
        price_matcher.add("PRICE", [pattern])

    matches = price_matcher(doc)
    for match_id, start, end in matches:
        price_span = doc[start:end]
        price = _extract_price_from_text(price_span.text)
        if price is not None:
            return price

    for token in doc:
        if token.text.lower() in price_keywords:
            start = max(0, token.i - window_size)
            end = min(len(doc), token.i + window_size)
            for tok in doc[start:end]:
                price = _extract_price_from_text(tok.text)
                if price is not None:
                    return price

    return None


# --- Main Extraction Functions ---
def extract_price(listing_html):
    """Extracts the price from an eBay listing HTML."""
    soup = BeautifulSoup(listing_html, 'html.parser')

    try:
        # 1. Try the existing selector
        price_element = soup.select_one('.s-item__price')
        if price_element:
            return _extract_price_from_text(price_element.text.strip())

        # 2. NLP-Based Extraction
        doc = nlp(soup.get_text())
        price = _extract_price_from_spacy_doc(doc)
        if price:
            return price

        # 3. Regex fallback
        price = _extract_price_from_text(soup.get_text())
        if price:
            return price

    except Exception as e:
        logger.error(f"Error extracting price: {e} - HTML: {listing_html}")

    return None

# --- Add similar robust extraction functions for other data points: ---
def extract_laptop_name(listing_html):
    """Extracts the laptop name from an eBay listing HTML."""
    soup = BeautifulSoup(listing_html, 'html.parser')
    try:
        name_element = soup.select_one('.s-item__title')
        if name_element:
            return name_element.text.strip()
    except Exception as e:
        logger.error(f"Error extracting laptop name: {e} - HTML: {listing_html}")
    return None


def extract_condition(listing_html):
    """Extracts the condition from an eBay listing HTML."""
    soup = BeautifulSoup(listing_html, 'html.parser')
    try:
        condition_element = soup.select_one('.s-item__subtitle')
        if condition_element:
            return condition_element.text.strip()
    except Exception as e:
        logger.error(f"Error extracting condition: {e} - HTML: {listing_html}")
    return None

def extract_laptop_name(listing_html):
    """Extracts the laptop name from an eBay listing HTML."""
    soup = BeautifulSoup(listing_html, 'html.parser')
    try:
        name_element = soup.select_one('.s-item__title')
        if name_element:
            return name_element.text.strip()
    except Exception as e:
        logger.error(f"Error extracting laptop name: {e} - HTML: {listing_html}")
    return None

def extract_shipping_cost(listing_html):
    """Extracts the shipping cost from an eBay listing HTML."""
    soup = BeautifulSoup(listing_html, 'html.parser')
    try:
        shipping_element = soup.select_one('.s-item__shipping')
        if shipping_element:
            return shipping_element.text.strip()
    except Exception as e:
        logger.error(f"Error extracting shipping cost: {e} - HTML: {listing_html}")
    return None

def extract_url(listing_html):
    """Extracts the URL from an eBay listing HTML."""
    soup = BeautifulSoup(listing_html, 'html.parser')
    try:
        url_element = soup.select_one('.s-item__link')
        if url_element:
            return url_element.get('href')
    except Exception as e:
        logger.error(f"Error extracting URL: {e} - HTML: {listing_html}")
    return None

