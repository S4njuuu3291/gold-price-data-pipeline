import logging
import requests
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, field_validator, ConfigDict
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from src.utils import get_secret_value, PROJECT_ID

logger = logging.getLogger(__name__)


class GoldPriceData(BaseModel):
    """Pydantic model for gold price data"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Gold",
                "price": 5196.299805,
                "symbol": "XAU",
                "updatedAt": "2026-02-27T13:09:24+0700",
                "updatedAtReadable": "a few seconds ago"
            }
        }
    )
    
    name: str = Field(..., description="Name of the commodity")
    price: float = Field(..., description="Current price")
    symbol: str = Field(..., description="Symbol of the commodity")
    updatedAt: str = Field(..., description="Timestamp of last update")
    updatedAtReadable: str = Field(..., description="Human readable timestamp")
    
    @field_validator('price')
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Price must be positive")
        return v
    
    @field_validator('symbol')
    @classmethod
    def symbol_must_not_be_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Symbol cannot be empty")
        return v


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    reraise=True
)
def fetch_gold_price() -> GoldPriceData | None:
    """
    Fetch gold price from API with retry logic.
    
    Returns the gold price data converted to WIB timezone.
    Retries up to 3 times with exponential backoff.
    
    Returns:
        GoldPriceData: Validated gold price data or None if failed
    """
    try:
        logger.info("Fetching gold price from API...")
        
        # Get API URL from Secret Manager
        api_url = get_secret_value(PROJECT_ID, "GOLD_API_KEY")
        
        if not api_url:
            logger.error("Failed to retrieve API URL from Secret Manager")
            return None
        
        # Fetch data from API
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Raw API response received: {data}")
        
        # Convert timestamp from UTC to WIB (UTC+7)
        updated_at_utc = datetime.strptime(data['updatedAt'], "%Y-%m-%dT%H:%M:%SZ")
        updated_at_wib = updated_at_utc + timedelta(hours=7)
        data['updatedAt'] = updated_at_wib.strftime("%Y-%m-%dT%H:%M:%S") + "+0700"
        
        # Validate data with Pydantic
        gold_price = GoldPriceData(**data)
        logger.info(f"Gold price data validated successfully: {gold_price.model_dump()}")
        
        return gold_price
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching gold price: {e}")
        raise  # Re-raise to trigger retry logic
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching gold price: {e}")
        return None