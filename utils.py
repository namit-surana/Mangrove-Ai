import os
import logging
import aiohttp
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not PERPLEXITY_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY environment variable is not set")

async def query_perplexity(domain: str, product: str, origin: str, destination: str) -> Dict[str, Any]:
    """
    Query the Perplexity API for regulatory certifications for a given domain.
    
    Args:
        domain (str): The domain to search for
        product (str): Name of the product to export
        origin (str): Country of origin
        destination (str): Destination country
        
    Returns:
        Dict[str, Any]: The response from Perplexity API
    """
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar-pro",
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": "You are a global trade compliance assistant. Respond only with official and verifiable regulatory data from trusted sources (e.g., Eur-Lex, FDA, DGFT, WTO, etc.). Format your response strictly as JSON. Do not include commentary, markdown, or assumptions. Only output the final structured JSON."
            },
            {
                "role": "user",
                "content": f"Identify all certifications, licenses, and regulatory approvals required to legally export the product {product} from {origin} and sell or distribute it in {destination}. For each requirement, return the following fields:\n"
                          f"- certificate_name: The name of the certification or license\n"
                          f"- certificate_description: A short explanation of what the certificate is and why it's required\n"
                          f"- legal_regulation: The name and article of the law or directive that mandates this (e.g., Regulation (EC) No 1223/2009, Article 19)\n"
                          f"- legal_text_excerpt: An exact quote (1–2 lines) from the regulation\n"
                          f"- legal_text_meaning: A simplified explanation of the quoted text\n"
                          f"- registration_fee: The official registration or filing fee, if publicly available (include currency and link if possible and convert to approximate USD (e.g., 'INR 500 (~$6.00 USD)')\n"
                          f"Return the result as a JSON array using exactly these field names: certificate_name, certificate_description, legal_regulation, legal_text_excerpt, legal_text_meaning, registration_fee"
            }
        ],
        "search_domain_filter": [domain],
        "include_search_results": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "domain": domain,
                        "product": product,
                        "origin": origin,
                        "destination": destination,
                        "response": result
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Error querying Perplexity API for domain {domain}: {error_text}")
                    return {
                        "domain": domain,
                        "product": product,
                        "origin": origin,
                        "destination": destination,
                        "error": f"API request failed with status {response.status}",
                        "details": error_text
                    }
    except Exception as e:
        logger.error(f"Exception while querying Perplexity API for domain {domain}: {str(e)}")
        return {
            "domain": domain,
            "product": product,
            "origin": origin,
            "destination": destination,
            "error": "Request failed",
            "details": str(e)
        }

async def process_domains(domains: List[str], product: str, origin: str, destination: str) -> List[Dict[str, Any]]:
    """
    Process multiple domains in parallel using the Perplexity API.
    
    Args:
        domains (List[str]): List of domains to process
        product (str): Name of the product to export
        origin (str): Country of origin
        destination (str): Destination country
        
    Returns:
        List[Dict[str, Any]]: List of results for each domain
    """
    tasks = [query_perplexity(domain, product, origin, destination) for domain in domains]
    return await asyncio.gather(*tasks) 