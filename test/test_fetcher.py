import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.publisher.fetcher import fetch_gold_price, GoldPriceData


@pytest.fixture
def mock_gold_data():
    """Fixture for mock gold data"""
    return {
        "name": "Gold",
        "price": 5196.299805,
        "symbol": "XAU",
        "updatedAt": "2026-02-27T06:09:24Z",
        "updatedAtReadable": "a few seconds ago"
    }


@patch('src.publisher.fetcher.get_secret_value')
@patch('src.publisher.fetcher.requests.get')
def test_fetch_gold_price_success(mock_get, mock_get_secret, mock_gold_data):
    """Test successful fetch of gold price"""
    # Setup mocks
    mock_get_secret.return_value = "https://api.example.com/gold"
    mock_response = MagicMock()
    mock_response.json.return_value = mock_gold_data
    mock_get.return_value = mock_response
    
    # Call function
    result = fetch_gold_price()
    
    # Assertions
    assert result is not None
    assert isinstance(result, GoldPriceData)
    assert result.name == "Gold"
    assert result.price == 5196.299805
    assert result.symbol == "XAU"


@patch('src.publisher.fetcher.get_secret_value')
def test_fetch_gold_price_no_api_url(mock_get_secret):
    """Test fetch when API URL cannot be retrieved"""
    # Setup mock to return None
    mock_get_secret.return_value = None
    
    # Call function
    result = fetch_gold_price()
    
    # Should return None
    assert result is None


@patch('src.publisher.fetcher.get_secret_value')
@patch('src.publisher.fetcher.requests.get')
def test_fetch_gold_price_request_exception(mock_get, mock_get_secret):
    """Test fetch when request fails"""
    import requests
    
    # Setup mocks
    mock_get_secret.return_value = "https://api.example.com/gold"
    mock_get.side_effect = requests.exceptions.RequestException("Connection failed")
    
    # Should raise after retries exhaust
    with pytest.raises(requests.exceptions.RequestException):
        fetch_gold_price()


def test_gold_price_data_validation_success(mock_gold_data):
    """Test GoldPriceData validation with valid data"""
    # Create valid instance
    data = GoldPriceData(**mock_gold_data)
    
    assert data.price == 5196.299805
    assert data.symbol == "XAU"


def test_gold_price_data_validation_negative_price(mock_gold_data):
    """Test GoldPriceData validation fails with negative price"""
    invalid_data = mock_gold_data.copy()
    invalid_data["price"] = -100
    
    with pytest.raises(ValueError):
        GoldPriceData(**invalid_data)


def test_gold_price_data_validation_empty_symbol(mock_gold_data):
    """Test GoldPriceData validation fails with empty symbol"""
    invalid_data = mock_gold_data.copy()
    invalid_data["symbol"] = ""
    
    with pytest.raises(ValueError):
        GoldPriceData(**invalid_data)


@patch('src.publisher.fetcher.get_secret_value')
@patch('src.publisher.fetcher.requests.get')
def test_fetch_gold_price_timezone_conversion(mock_get, mock_get_secret, mock_gold_data):
    """Test that timezone is correctly converted from UTC to WIB"""
    # Setup mocks
    mock_get_secret.return_value = "https://api.example.com/gold"
    test_data = mock_gold_data.copy()
    test_data["updatedAt"] = "2026-02-27T06:00:00Z"  # UTC time
    
    mock_response = MagicMock()
    mock_response.json.return_value = test_data
    mock_get.return_value = mock_response
    
    # Call function
    result = fetch_gold_price()
    
    # Check that time was converted (UTC+7)
    assert result is not None
    # Should contain +0700 timezone offset (WIB)
    assert "+0700" in result.updatedAt

