import re
import traceback

from loguru import logger

from modules.natural_language_processor import NaturalLanguageProcessor

nlp = NaturalLanguageProcessor()

# Regex patterns
price_patterns = [
    r'(\$\d+(?:\.\d{2})?)',  # Pattern 1: Matches prices like $337.99
    r'(\$\d+(?:\.\d{2})?)\s+to\s+(\$\d+(?:\.\d{2})?)',  # Pattern 2: Matches price ranges like $131.59 to $345.59
    r'(\d+\s+000\s+тенге)',  # Pattern 3: Matches prices like 125 000 тенге
]

# Regex patterns
shipping_patterns = [
    r'Free shipping',  # Pattern 1: Matches 'Free shipping'
    r'\+\$(\d+\.\d{2}) shipping',  # Pattern 2: Matches prices like +$20.00 shipping
    r'Free local pickup',  # Pattern 3: Matches 'Free local pickup'
]

async def extract_data_nlp(listing, element_name):
    """
    Extracts data from a listing using natural language processing.

    Args:
        listing: The listing to extract data from.
        element_name: The name of the element to extract.

    Returns:
        The extracted data, or "N/A" if the data could not be extracted.
    """
    logger.error(f'Extracting data nlp for {element_name}...')
    html_content = await listing.content()
    soup = nlp.clean_html(html_content)
    text = nlp.extract_relevant_text(soup, element_name)
    tokens = nlp.process_text(text)
    element = nlp.find_element(element_name, tokens)
    if element:
        element_code = nlp.get_element_code(soup, element)
        logger.error(f"Extracted data nlp {element_name}: {element_code}")
        return element_code
    else:
        return "N/A"


async def extract_element(listing, css_selector, element_name):
    logger.info(f"Extracting {element_name}...")
    try:
        elements = await listing.locator(css_selector).all()
        if not elements:
            return "N/A"
        texts = await get_visible_texts(elements)
        logger.info(f"Extracted {element_name}: {texts}")
        return await handle_special_cases(element_name, elements, texts)
    except Exception as e:
        logger.error(f"Error extracting {element_name}: {e}")
        logger.error(traceback.format_exc())
        return await extract_data_nlp(listing, element_name)


async def get_visible_texts(elements):
    texts = []
    for element in elements:
        if await element.is_visible():
            text = await element.text_content()
            texts.append(text)
    return texts

# Function to apply regex patterns
async def extract_prices(strings, patterns):
    results = []
    for string in strings:
        matched = False
        for pattern in patterns:
            match = re.findall(pattern, string)
            if match:
                matched = True
                # Join multiple prices with a comma
                results.append(', '.join(match))
                break
        if not matched:
            results.append("N/A")
    return results

async def extract_shipping_info(strings, patterns):
    results = []
    for string in strings:
        matched = False
        for pattern in patterns:
            if re.search(pattern, string):
                matched = True
                # Check for free shipping or local pickup
                if 'Free shipping' in string:
                    results.append('Free')
                elif 'Free local pickup' in string:
                    results.append('Local')
                else:
                    # Extract the shipping cost
                    match = re.search(r'\$(\d+\.\d{2})', string)
                    if match:
                        results.append(match.group(1))
                break
        if not matched:
            results.append("No shipping info")
    return results


async def handle_special_cases(element_name, elements, texts):
    if element_name in ["url"]:
        url = await elements[0].get_attribute('href')
        logger.info(f"Extracted {element_name}: {url}")
        return url
    if element_name in ["price"]:
        price_texts = await extract_prices(texts, price_patterns)
        # # Remove non-numeric characters before converting
        # price_texts = [re.sub(r"[^\d\.]", "", text) for text in texts]
        return price_texts
    if element_name in ["shipping cost"]:
        return await extract_shipping_info(texts, shipping_patterns)
        # return await handle_shipping_cost(texts)
    if element_name in ["time left"]:
        logger.info(f"Extracted time left: {texts}")
        return [text.strip() for text in texts]
    return [text.strip() for text in texts]


async def handle_shipping_cost(texts):
    if any('Free' in text or 'Бесплатная' in text for text in texts):
        logger.info(f"Extracted shipping cost: {0.00}")
        return 0.00
    else:
        shipping_costs = [re.findall(r"[\d\.]+", text) for text in texts]
        logger.info(f"Extracted shipping cost: {shipping_costs}")
        if shipping_costs:
            return [str(cost[0]) for cost in shipping_costs if cost]
        else:
            return "N/A"
