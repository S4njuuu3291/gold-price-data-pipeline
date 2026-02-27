import pytest
from unittest.mock import patch, MagicMock
import json
import base64
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.subscriber.main import receive_gold_price


@pytest.fixture
def mock_gold_price_message():
    """Fixture for mock gold price message data"""
    return {
        "name": "Gold",
        "price": 5196.299805,
        "symbol": "XAU",
        "updatedAt": "2026-02-27T13:09:24+0700",
        "updatedAtReadable": "a few seconds ago"
    }


@pytest.fixture
def valid_pubsub_push_request(mock_gold_price_message):
    """Fixture for valid Pub/Sub push request"""
    mock_request = MagicMock()
    
    # Encode message data to base64
    message_data = json.dumps(mock_gold_price_message)
    message_data_b64 = base64.b64encode(message_data.encode()).decode()
    
    mock_request.get_json.return_value = {
        "message": {
            "data": message_data_b64,
            "messageId": "test-message-123",
            "publishTime": "2026-02-27T12:00:00.000Z",
            "attributes": {}
        },
        "subscription": "projects/gold-price-alert-488703/subscriptions/gold-price-alert-488703-topic-subscription"
    }
    
    return mock_request


def test_receive_gold_price_success(valid_pubsub_push_request):
    """Test successful processing of gold price message"""
    response, status_code = receive_gold_price(valid_pubsub_push_request)
    
    assert status_code == 200
    assert response['status'] == 'success'
    assert 'timestamp' in response
    assert response['messageId'] == 'test-message-123'
    assert 'data' in response
    assert response['data']['symbol'] == 'XAU'
    assert response['data']['price'] == 5196.299805


def test_receive_gold_price_no_request():
    """Test when no request is provided"""
    response, status_code = receive_gold_price(None)
    
    assert status_code == 400
    assert response['status'] == 'error'
    assert 'No request' in response['message']
    assert 'timestamp' in response


def test_receive_gold_price_invalid_json():
    """Test when request body is not valid JSON"""
    mock_request = MagicMock()
    mock_request.get_json.return_value = None
    
    response, status_code = receive_gold_price(mock_request)
    
    assert status_code == 400
    assert response['status'] == 'error'
    assert 'Request body is not JSON' in response['message']


def test_receive_gold_price_missing_message_field():
    """Test when message field is missing in request"""
    mock_request = MagicMock()
    mock_request.get_json.return_value = {
        "subscription": "projects/test/subscriptions/test-sub"
    }
    
    response, status_code = receive_gold_price(mock_request)
    
    assert status_code == 400
    assert response['status'] == 'error'
    assert "missing 'message' field" in response['message']


def test_receive_gold_price_missing_data_field():
    """Test when data field is missing in message"""
    mock_request = MagicMock()
    mock_request.get_json.return_value = {
        "message": {
            "messageId": "test-123",
            "publishTime": "2026-02-27T12:00:00.000Z"
        },
        "subscription": "projects/test/subscriptions/test-sub"
    }
    
    response, status_code = receive_gold_price(mock_request)
    
    assert status_code == 400
    assert response['status'] == 'error'
    assert "missing 'data' field" in response['message']


def test_receive_gold_price_invalid_base64():
    """Test when base64 data is invalid"""
    mock_request = MagicMock()
    mock_request.get_json.return_value = {
        "message": {
            "data": "not-valid-base64!!!",
            "messageId": "test-123",
            "publishTime": "2026-02-27T12:00:00.000Z"
        },
        "subscription": "projects/test/subscriptions/test-sub"
    }
    
    response, status_code = receive_gold_price(mock_request)
    
    assert status_code == 400
    assert response['status'] == 'error'
    assert 'Failed to decode base64' in response['message']


def test_receive_gold_price_invalid_json_in_message():
    """Test when decoded message is not valid JSON"""
    mock_request = MagicMock()
    
    # Create invalid JSON that is valid base64
    invalid_json = "not a json message"
    invalid_json_b64 = base64.b64encode(invalid_json.encode()).decode()
    
    mock_request.get_json.return_value = {
        "message": {
            "data": invalid_json_b64,
            "messageId": "test-123",
            "publishTime": "2026-02-27T12:00:00.000Z"
        },
        "subscription": "projects/test/subscriptions/test-sub"
    }
    
    response, status_code = receive_gold_price(mock_request)
    
    assert status_code == 400
    assert response['status'] == 'error'
    assert 'Failed to parse message JSON' in response['message']
    assert response['messageId'] == 'test-123'


def test_receive_gold_price_response_format(valid_pubsub_push_request):
    """Test response format is correct"""
    response, status_code = receive_gold_price(valid_pubsub_push_request)
    
    # Verify response structure
    assert isinstance(response, dict)
    assert 'status' in response
    assert 'message' in response
    assert 'timestamp' in response
    assert 'messageId' in response
    assert 'data' in response
    assert isinstance(status_code, int)
    
    # Verify data structure
    assert 'symbol' in response['data']
    assert 'price' in response['data']
    assert 'updatedAt' in response['data']


def test_receive_gold_price_with_attributes(valid_pubsub_push_request):
    """Test processing message with attributes"""
    response, status_code = receive_gold_price(valid_pubsub_push_request)
    
    # Should still work with attributes in message
    assert status_code == 200
    assert response['status'] == 'success'


def test_receive_gold_price_message_id_in_response(valid_pubsub_push_request):
    """Test that messageId is properly returned in response"""
    response, status_code = receive_gold_price(valid_pubsub_push_request)
    
    assert response['messageId'] == 'test-message-123'
    assert 'successfully' in response['message'].lower()


def test_receive_gold_price_empty_gene_data():
    """Test with minimal but valid message"""
    mock_request = MagicMock()
    
    # Minimal gold price data
    minimal_data = json.dumps({"symbol": "XAU", "price": 100.00})
    message_data_b64 = base64.b64encode(minimal_data.encode()).decode()
    
    mock_request.get_json.return_value = {
        "message": {
            "data": message_data_b64,
            "messageId": "minimal-test-123"
        },
        "subscription": "projects/test/subscriptions/test-sub"
    }
    
    response, status_code = receive_gold_price(mock_request)
    
    assert status_code == 200
    assert response['status'] == 'success'
    assert response['data']['symbol'] == 'XAU'
    assert response['data']['price'] == 100.00


def test_receive_gold_price_handles_utf8():
    """Test proper UTF-8 handling of message data"""
    mock_request = MagicMock()
    
    # Message with special characters
    data_with_utf8 = json.dumps({
        "name": "Emas (Gold)",  # Emas is gold in Indonesian
        "symbol": "XAU",
        "price": 5196.30
    })
    message_data_b64 = base64.b64encode(data_with_utf8.encode('utf-8')).decode()
    
    mock_request.get_json.return_value = {
        "message": {
            "data": message_data_b64,
            "messageId": "utf8-test-123"
        },
        "subscription": "projects/test/subscriptions/test-sub"
    }
    
    response, status_code = receive_gold_price(mock_request)
    
    assert status_code == 200
    assert response['status'] == 'success'
