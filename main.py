import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from utils import process_domains, deduplicate_certifications_with_llm
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Regulatory Certification Search API",
    description="API to search for regulatory certifications using Perplexity AI",
    version="1.0.0"
)

class SearchRequest(BaseModel):
    user_question: str = Field(..., description="User's question to find regulatory certifications, from which product, origin, and destination will be extracted")
    domains: List[str] = Field(..., min_items=1, description="List of domains to search for regulatory certifications")

class CertificationResponse(BaseModel):
    certificate_name: str
    certificate_description: str
    legal_regulation: str
    legal_text_excerpt: str
    legal_text_meaning: str
    registration_fee: str

def reformat_results(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    combined_certifications = []
    results = data.get("results", [])

    for entry in results:
        domain = entry.get("domain")
        response_content = (
            entry.get("response", {})
                 .get("choices", [{}])[0]
                 .get("message", {})
                 .get("content")
        )

        if response_content:
            try:
                certs_from_domain = json.loads(response_content)
                if isinstance(certs_from_domain, list):
                    for cert in certs_from_domain:
                        cert['domain'] = domain  # Add domain to each cert
                        combined_certifications.append(cert)
                elif isinstance(certs_from_domain, dict) and "error" in certs_from_domain:
                    logger.warning(f"Domain {domain} returned an error in content: {certs_from_domain.get('message', '')}")
                else:
                    logger.warning(f"Unexpected content format from domain {domain}: {response_content[:100]}...")
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from domain {domain} content: {response_content[:100]}...")
        elif "error" in entry:
            logger.error(f"Top-level error for domain {domain}: {entry.get('details', '')}")

    return combined_certifications

@app.post("/search")
async def search_certifications(request: SearchRequest) -> Dict[str, Any]:
    start_time = time.time()  # Start timer
    try:
        if not request.domains:
            raise HTTPException(status_code=400, detail="No domains provided")
            
        logger.info(f"Processing request for user question: {request.user_question}")
        logger.info(f"Processing {len(request.domains)} domains: {', '.join(request.domains)}")
        
        results = await process_domains(
            domains=request.domains,
            user_question=request.user_question
        )
        
        elapsed = time.time() - start_time  # End timer
        logger.info(f"Total time taken for /search: {elapsed:.2f} seconds")
        
        # Log successful results and any errors
        for result in results:
            if "error" not in result:
                logger.info(f"Successfully processed domain: {result['domain']}")
                if "response" in result and "choices" in result["response"]:
                    # Log length of choices in response, not response itself
                    content = result['response']['choices'][0]['message']['content']
                    try:
                        parsed_content = json.loads(content)
                        if isinstance(parsed_content, list):
                            logger.info(f"Found {len(parsed_content)} certification requirements for {result['domain']}")
                        else:
                            logger.info(f"Domain {result['domain']} returned non-list content.")
                    except json.JSONDecodeError:
                        logger.info(f"Domain {result['domain']} returned non-JSON content.")
            else:
                logger.error(f"Failed to process domain {result['domain']}: {result['error']}")
                if "details" in result:
                    logger.error(f"Error details: {result['details']}")
        
        # Reformat the results using the new logic
        formatted_results = reformat_results({"results": results})
        
        # Deduplicate the results using LLM
        deduplicated_results = await deduplicate_certifications_with_llm(formatted_results)

        return {
            "elapsed_seconds": round(elapsed, 2),
            "results": deduplicated_results
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

def convert_to_markdown(certifications: List[Dict[str, Any]]) -> str:
    """
    Convert certification results to markdown format.
    
    Args:
        certifications (List[Dict[str, Any]]): List of certification requirements
        
    Returns:
        str: Markdown formatted string
    """
    markdown = "# Required Certifications and Regulatory Requirements\n\n"
    
    # Generate markdown for each certification sequentially
    for i, cert in enumerate(certifications, 1):
        markdown += f"## {i}. {cert['certificate_name']}\n\n"
        markdown += f"**Source Domain:** {cert['domain']}\n\n"
        markdown += f"**Description:** {cert['certificate_description']}\n\n"
        markdown += f"**Legal Regulation:** {cert['legal_regulation']}\n\n"
        markdown += f"**Legal Text Excerpt:**\n> {cert['legal_text_excerpt']}\n\n"
        markdown += f"**Legal Text Meaning:** {cert['legal_text_meaning']}\n\n"
        markdown += f"**Registration Fee:** {cert['registration_fee']}\n\n"
        markdown += "---\n\n"
    
    return markdown

@app.post("/search/markdown")
async def search_certifications_markdown(request: SearchRequest) -> Dict[str, Any]:
    """
    Search for certifications and return results in markdown format.
    """
    try:
        # First get the regular search results
        search_results = await search_certifications(request)
        
        # Convert the results to markdown
        markdown_content = convert_to_markdown(search_results["results"])
        
        return {
            "elapsed_seconds": search_results["elapsed_seconds"],
            "markdown": markdown_content
        }
        
    except Exception as e:
        logger.error(f"Error processing markdown request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 