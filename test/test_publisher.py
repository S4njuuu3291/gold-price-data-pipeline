import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.publisher.publisher import publish_to_pubsub


@patch('src.publisher.publisher.pubsub.PublisherClient')
def test_publish_to_pubsub_success(mock_publisher_client):
    """Test successful publish to Pub/Sub"""
    # Setup mock
    mock_client = MagicMock()
    mock_publisher_client.return_value = mock_client
    mock_future = MagicMock()
    mock_client.publish.return_value = mock_future
    mock_future.result.return_value = None
    
    # Call function
    publish_to_pubsub("test-project", "test-topic", "test message")
    
    # Assertions
    mock_client.topic_path.assert_called_once_with("test-project", "test-topic")
    mock_client.publish.assert_called_once()
    mock_future.result.assert_called_once()


@patch('src.publisher.publisher.pubsub.PublisherClient')
def test_publish_to_pubsub_with_different_data(mock_publisher_client):
    """Test publishing different data types"""
    # Setup mock
    mock_client = MagicMock()
    mock_publisher_client.return_value = mock_client
    mock_future = MagicMock()
    mock_client.publish.return_value = mock_future
    
    test_data = '{"name": "Gold", "price": 5196.30, "symbol": "XAU"}'
    
    # Call function
    publish_to_pubsub("my-project", "gold-topic", test_data)
    
    # Verify publish was called with encoded data
    call_args = mock_client.publish.call_args
    assert call_args[0][1] == test_data.encode("utf-8")


@patch('src.publisher.publisher.pubsub.PublisherClient')
def test_publish_to_pubsub_handles_exception(mock_publisher_client):
    """Test that exceptions are handled gracefully"""
    # Setup mock to raise exception
    mock_client = MagicMock()
    mock_publisher_client.return_value = mock_client
    mock_client.publish.side_effect = Exception("Connection error")
    
    # Should not raise, just log error
    try:
        publish_to_pubsub("test-project", "test-topic", "test")
    except Exception as e:
        pytest.fail(f"publish_to_pubsub raised {type(e).__name__} unexpectedly")

