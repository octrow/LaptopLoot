import re
import traceback

from loguru import logger

from modules.natural_language_processor import NaturalLanguageProcessor

nlp = NaturalLanguageProcessor()


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
    soup = nlp.parse_html(html_content)
    text = nlp.extract_text(soup)
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


async def handle_special_cases(element_name, elements, texts):
    if element_name in ["url"]:
        url = await elements[0].get_attribute('href')
        logger.info(f"Extracted {element_name}: {url}")
        return url
    if element_name in ["price"]:
        # Remove non-numeric characters before converting
        price_texts = [re.sub(r"[^\d\.]", "", text) for text in texts]
        return price_texts
    if element_name in ["shipping cost"]:
        return await handle_shipping_cost(texts)
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
