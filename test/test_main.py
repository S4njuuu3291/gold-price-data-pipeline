import pytest
from unittest.mock import patch, MagicMock
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.publisher.main import publish_gold_price


@pytest.fixture
def mock_gold_data():
    """Fixture for mock gold data"""
    return {
        "name": "Gold",
        "price": 5196.299805,
        "symbol": "XAU",
        "updatedAt": "2026-02-27T13:09:24+0700",
        "updatedAtReadable": "a few seconds ago"
    }


@patch('src.publisher.main.publish_to_pubsub')
@patch('src.publisher.main.fetch_gold_price')
def test_publish_gold_price_success(mock_fetch, mock_publish, mock_gold_data):
    """Test successful publish of gold price"""
    # Setup mocks
    from src.publisher.fetcher import GoldPriceData
    mock_fetch.return_value = GoldPriceData(**mock_gold_data)
    mock_publish.return_value = None
    
    # Call function
    response, status_code = publish_gold_price()
    
    # Assertions
    assert status_code == 200
    assert response['status'] == 'success'
    assert 'timestamp' in response
    assert 'data' in response
    assert response['data']['symbol'] == 'XAU'
    assert response['data']['price'] == 5196.299805
    mock_fetch.assert_called_once()
    mock_publish.assert_called_once()


@patch('src.publisher.main.fetch_gold_price')
def test_publish_gold_price_fetch_failure(mock_fetch):
    """Test when fetch_gold_price returns None"""
    # Setup mock to return None
    mock_fetch.return_value = None
    
    # Call function
    response, status_code = publish_gold_price()
    
    # Assertions
    assert status_code == 500
    assert response['status'] == 'error'
    assert 'Failed to fetch' in response['message']
    assert 'timestamp' in response


@patch('src.publisher.main.publish_to_pubsub')
@patch('src.publisher.main.fetch_gold_price')
def test_publish_gold_price_publish_exception(mock_fetch, mock_publish, mock_gold_data):
    """Test when publish_to_pubsub raises exception"""
    from src.publisher.fetcher import GoldPriceData
    
    # Setup mocks
    mock_fetch.return_value = GoldPriceData(**mock_gold_data)
    mock_publish.side_effect = Exception("Publish failed")
    
    # Call function
    response, status_code = publish_gold_price()
    
    # Assertions
    assert status_code == 500
    assert response['status'] == 'error'
    assert 'Error in publish_gold_price' in response['message']


@patch('src.publisher.main.publish_to_pubsub')
@patch('src.publisher.main.fetch_gold_price')
def test_publish_gold_price_response_format(mock_fetch, mock_publish, mock_gold_data):
    """Test response format is correct"""
    from src.publisher.fetcher import GoldPriceData
    
    # Setup mocks
    mock_fetch.return_value = GoldPriceData(**mock_gold_data)
    mock_publish.return_value = None
    
    # Call function
    response, status_code = publish_gold_price()
    
    # Verify response structure
    assert isinstance(response, dict)
    assert 'status' in response
    assert 'timestamp' in response
    assert 'data' in response
    assert isinstance(status_code, int)
    assert response['data']['symbol'] == 'XAU'
    assert isinstance(status_code, int)


@patch('src.publisher.main.fetch_gold_price')
def test_publish_gold_price_exception_handling(mock_fetch):
    """Test general exception handling"""
    # Setup mock to raise unexpected exception
    mock_fetch.side_effect = RuntimeError("Unexpected error")
    
    # Call function should handle exception
    response, status_code = publish_gold_price()
    
    # Assertions
    assert status_code == 500
    assert response['status'] == 'error'
    assert 'Error in publish_gold_price' in response['message']

