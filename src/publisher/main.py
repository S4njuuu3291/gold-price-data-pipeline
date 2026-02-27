import json
import logging
from typing import Any, Tuple, Dict, Optional
from datetime import datetime, timezone
from src.publisher.fetcher import fetch_gold_price
from src.publisher.publisher import publish_to_pubsub
from src.utils import PROJECT_ID, TOPIC_ID

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def publish_gold_price(request: Optional[Any] = None) -> Tuple[Dict[str, Any], int]:
    """
    Google Cloud Function entry point to fetch and publish gold price to Pub/Sub.
    
    This function is designed to be triggered by:
    1. Cloud Scheduler (HTTP request)
    2. Cloud Function HTTP trigger
    3. Local testing (with request=None)
    
    Args:
        request: Flask request object from Cloud Function environment.
                 Can be None for local testing, or provided by Cloud Function runtime.
    
    Returns:
        Tuple[Dict, int]: (response_dict, status_code)
            - response_dict contains: status, message, timestamp, and optional data
            - status_code: HTTP status code (200, 500)
    
    Raises:
        None - All exceptions are caught and logged with proper error response
    """
    
    # Log invocation details
    timestamp = datetime.now(timezone.utc).isoformat()
    invocation_source = "Cloud Scheduler/HTTP" if request else "Local/Test"
    logger.info(
        f"Gold price publisher triggered by {invocation_source} | "
        f"Timestamp: {timestamp}"
    )
    
    try:
        # Fetch gold price with retry logic
        logger.info("Fetching gold price data...")
        gold_data = fetch_gold_price()
        
        if gold_data is None:
            error_msg = "Failed to fetch gold price data - returned None"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "timestamp": timestamp
            }, 500
        
        logger.info(f"Gold price fetched successfully: {gold_data.symbol}={gold_data.price}")
        
        # Convert to JSON string for Pub/Sub
        gold_dict = gold_data.model_dump()
        message_data = json.dumps(gold_dict)
        logger.info(f"Publishing message to topic: {TOPIC_ID}")
        
        # Publish to Pub/Sub
        publish_to_pubsub(PROJECT_ID, TOPIC_ID, message_data)
        
        logger.info(f"Successfully published gold price to Pub/Sub")
        
        response = {
            "status": "success",
            "message": "Gold price fetched and published successfully",
            "timestamp": timestamp,
            "data": {
                "symbol": gold_data.symbol,
                "price": gold_data.price,
                "updatedAt": gold_data.updatedAt
            }
        }
        logger.info(f"Publisher execution completed successfully")
        
        return response, 200
        
    except Exception as e:
        error_timestamp = datetime.now(timezone.utc).isoformat()
        error_msg = f"Error in publish_gold_price: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            "status": "error",
            "message": error_msg,
            "timestamp": error_timestamp
        }, 500


if __name__ == "__main__":
    # For local testing
    print("Testing publisher function locally...")
    response, status_code = publish_gold_price(request=None)
    print(f"Status Code: {status_code}")
    print(f"Response: {json.dumps(response, indent=2)}")

