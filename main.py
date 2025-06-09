import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from utils import process_domains
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Regulatory Certification Search API",
    description="API to search for regulatory certifications using Perplexity AI",
    version="1.0.0"
)

class SearchRequest(BaseModel):
    product: str = Field(..., description="Name of the product to export")
    origin: str = Field(..., description="Country of origin")
    destination: str = Field(..., description="Destination country")
    domains: List[str] = Field(..., min_items=1, description="List of domains to search for regulatory certifications")

class CertificationResponse(BaseModel):
    certificate_name: str
    certificate_description: str
    legal_regulation: str
    legal_text_excerpt: str
    legal_text_meaning: str
    registration_fee: str

@app.post("/search")
async def search_certifications(request: SearchRequest) -> Dict[str, Any]:
    start_time = time.time()  # Start timer
    try:
        if not request.domains:
            raise HTTPException(status_code=400, detail="No domains provided")
            
        logger.info(f"Processing request for product: {request.product}")
        logger.info(f"Trade route: {request.origin} -> {request.destination}")
        logger.info(f"Processing {len(request.domains)} domains: {', '.join(request.domains)}")
        
        results = await process_domains(
            domains=request.domains,
            product=request.product,
            origin=request.origin,
            destination=request.destination
        )
        
        elapsed = time.time() - start_time  # End timer
        logger.info(f"Total time taken for /search: {elapsed:.2f} seconds")
        
        # Log successful results and any errors
        for result in results:
            if "error" not in result:
                logger.info(f"Successfully processed domain: {result['domain']}")
                if "response" in result and "choices" in result["response"]:
                    logger.info(f"Found {len(result['response']['choices'])} certification requirements for {result['domain']}")
            else:
                logger.error(f"Failed to process domain {result['domain']}: {result['error']}")
                if "details" in result:
                    logger.error(f"Error details: {result['details']}")
        
        return {"elapsed_seconds": round(elapsed, 2), "results": results}
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"} 