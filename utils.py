import os
import logging
import aiohttp
import asyncio
import json
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

async def extract_info_from_question(user_question: str) -> Dict[str, str]:
    """
    Extracts product, origin, and destination from a user question using Perplexity AI.
    """
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar-pro",
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant specialized in extracting structured information from user questions. "
                    "Your task is to extract the following fields **only if clearly mentioned or confidently implied**:\n"
                    "- product: the item the user wants to export\n"
                    "- origin: the country where the product is made or shipped from\n"
                    "- destination: the country or region where the product will be sold or exported to\n\n"
                    "If a country is not mentioned but a company (e.g., 'Nike', 'The North Face') is mentioned, "
                    "you may infer the country of operation **only if it is widely known and unambiguous**. "
                    "If you're unsure about any field, leave it as an empty string.\n\n"
                    "Return ONLY a valid JSON object with exactly these keys: 'product', 'origin', 'destination'. "
                    "Do NOT include any extra commentary, explanation, or markdown. "
                    "Do NOT generate data that is not present or confidently inferable."
                )
            },
            {
                "role": "user",
                "content": (
                    f"The following is a user's question about exporting a product. "
                    f"Please extract the three key fields: 'product', 'origin', and 'destination'. "
                    f"If any of them are not clearly stated or confidently implied, leave them as an empty string.\n\n"
                    f"User question:\n{user_question}\n\n"
                    f"Return ONLY a valid JSON object with the keys: 'product', 'origin', 'destination'."
                )
            }
        ],
        "include_search_results": False
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    response_content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    
                    json_start = response_content.find('{')
                    json_end = response_content.rfind('}') + 1
                    
                    if json_start != -1 and json_end != -1:
                        json_str = response_content[json_start:json_end]
                        try:
                            extracted_data = json.loads(json_str)
                            return {
                                "product": extracted_data.get("product", ""),
                                "origin": extracted_data.get("origin", ""),
                                "destination": extracted_data.get("destination", "")
                            }
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON from Perplexity extraction: {json_str}")
                            return {"product": "", "origin": "", "destination": ""}
                    else:
                        logger.error(f"No JSON found in Perplexity extraction response: {response_content}")
                        return {"product": "", "origin": "", "destination": ""}

                else:
                    error_text = await response.text()
                    logger.error(f"Error querying Perplexity API for info extraction: {error_text}")
                    return {"product": "", "origin": "", "destination": ""}
    except Exception as e:
        logger.error(f"Exception while extracting info from user question: {str(e)}")
        return {"product": "", "origin": "", "destination": ""}

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
                          f"- registration_fee: The official registration or filing fee, if publicly available (include currency and link if possible and convert to approximate USD (e.g., 'INR 500 (~$6.00 USD)'))\n"
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

async def process_domains(domains: List[str], user_question: str) -> List[Dict[str, Any]]:
    """
    Process multiple domains in parallel using the Perplexity API,
    extracting product, origin, and destination from the user question.
    """
    logger.info(f"Extracting product, origin, and destination from: {user_question}")
    extracted_info = await extract_info_from_question(user_question)
    product = extracted_info.get("product", "")
    origin = extracted_info.get("origin", "")
    destination = extracted_info.get("destination", "")
    
    if not (product and origin and destination):
        logger.warning(f"Could not extract all required information (product, origin, destination) from user question: '{user_question}'. Proceeding with available info.")

    tasks = [query_perplexity(domain, product, origin, destination) for domain in domains]
    return await asyncio.gather(*tasks)

async def deduplicate_certifications_with_llm(certifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates a list of certifications using Perplexity AI to identify and consolidate similar entries.
    """
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    # Prepare the list of certifications as a string for the LLM
    certs_str = json.dumps(certifications, indent=2)

    messages = [
        {
            "role": "system",
            "content": "You are an expert in regulatory compliance and data consolidation. Your task is to review a list of certification requirements, identify and consolidate similar or duplicate certifications based on their 'certificate_name' and 'certificate_description'. For each unique certification, provide one comprehensive entry. If there are variations for the same certificate, use the most detailed and representative information. Ensure the output is a JSON array of unique certification objects, maintaining all original field names: 'certificate_name', 'certificate_description', 'legal_regulation', 'legal_text_excerpt', 'legal_text_meaning', 'registration_fee', and 'domain'. Do not include any other text, commentary, or markdown outside the JSON."
        },
        {
            "role": "user",
            "content": f"Here is the list of certifications:\n\n{certs_str}\n\nConsolidate and return only the unique certifications."
        }
    ]

    payload = {
        "model": "sonar-pro",
        "temperature": 0.1, # Keep temperature low for more deterministic results
        "messages": messages,
        "include_search_results": False
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    response_content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    
                    # Attempt to find JSON within the response content
                    json_start = response_content.find('[') # Expecting a JSON array
                    json_end = response_content.rfind(']') + 1
                    
                    if json_start != -1 and json_end != -1:
                        json_str = response_content[json_start:json_end]
                        try:
                            deduplicated_certs = json.loads(json_str)
                            if isinstance(deduplicated_certs, list):
                                return deduplicated_certs
                            else:
                                logger.error(f"Perplexity returned non-list JSON for deduplication: {json_str}")
                                return certifications # Return original if not a list
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON from Perplexity deduplication: {json_str}")
                            return certifications # Return original on decode error
                    else:
                        logger.error(f"No JSON array found in Perplexity deduplication response: {response_content}")
                        return certifications # Return original if no JSON found

                else:
                    error_text = await response.text()
                    logger.error(f"Error querying Perplexity API for deduplication: {error_text}")
                    return certifications # Return original on API error
    except Exception as e:
        logger.error(f"Exception while deduplicating certifications: {str(e)}")
        return certifications # Return original on exception 