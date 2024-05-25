import spacy
from spacy.matcher import Matcher
from bs4 import BeautifulSoup
import re
import logging

# Configure logging (adjust level as needed)
logging.basicConfig(filename='laptoploot_extraction.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

nlp = spacy.load("en_core_web_sm")

# --- Helper Functions ---
def _extract_price_from_text(text):
    """Extracts price from a string using regex. Handles commas, decimals,
       and multiple currencies. (You'll need to improve this regex).
    """
    price_match = re.search(r'(?:\$|£|€)\d+(?:,\d{3})*(?:\.\d{2})?', text)
    if price_match:
        return float(price_match.group(0)[1:].replace(',', ''))
    return None

def _extract_price_from_spacy_doc(doc, window_size=7):
    """Finds price-related entities and analyzes surrounding tokens."""
    price_keywords = ['price', 'cost', 'selling', 'buy', 'now', 'for']
    price_matcher = Matcher(nlp.vocab)
    price_pattern = [
        {"LIKE_NUM": True, "OP": "?"}, # Optional number before currency
        {"ORTH": "$", "OP": "|"},
        {"ORTH": "£", "OP": "|"},
        {"ORTH": "€", "OP": "|"},
        {"LIKE_NUM": True}
    ]
    price_matcher.add("PRICE", [price_pattern])

    for token in doc:
        if token.text.lower() in price_keywords:
            # Analyze neighbors for price-like patterns
            start = max(0, token.i - window_size)
            end = min(len(doc), token.i + window_size)
            for tok in doc[start:end]:
                if _extract_price_from_text(tok.text):
                    return _extract_price_from_text(tok.text)

    matches = price_matcher(doc)
    for match_id, start, end in matches:
        return _extract_price_from_text(doc[start:end].text)

    return None


# --- Main Extraction Functions ---
def extract_price(listing_html):
    """Extracts the price from an eBay listing HTML."""
    soup = BeautifulSoup(listing_html, 'html.parser')

    try:
        # 1. Try existing selector
        price_element = soup.select_one('.s-item__price')
        if price_element:
            return _extract_price_from_text(price_element.text.strip())

        # 2. NLP-Based Extraction
        doc = nlp(soup.get_text())
        price = _extract_price_from_spacy_doc(doc)
        if price:
            return price

        # 3. Fallback: Regex on entire text
        price = _extract_price_from_text(soup.get_text())
        if price:
            return price

    except Exception as e:
        logging.error(f"Error extracting price: {e} - HTML: {listing_html}")
    return None

# --- Add Similar Functions for: extract_laptop_name, extract_condition, etc. ---
# (Follow the same structure: selectors first, then NLP, then regex fallback)