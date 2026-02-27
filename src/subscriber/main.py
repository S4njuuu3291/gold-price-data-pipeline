import json
import logging
import base64
from typing import Any, Dict, Tuple, Optional
from datetime import datetime, timezone

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def receive_gold_price(request: Any) -> Tuple[Dict[str, Any], int]:
    """
    Cloud Function entry point to receive and process gold price messages from Pub/Sub.
    
    This function is designed to be triggered by Cloud Pub/Sub in PUSH mode.
    The subscription pushes messages to this Cloud Function via HTTP POST requests.
    
    Request format (Pub/Sub push envelope):
    {
        "message": {
            "data": "base64-encoded-message",
            "messageId": "...",
            "publishTime": "2026-02-27T12:00:00.000Z",
            "attributes": {}
        },
        "subscription": "projects/.../subscriptions/..."
    }
    
    Args:
        request: Flask request object from Cloud Function environment.
                 Contains Pub/Sub push message in JSON body.
    
    Returns:
        Tuple[Dict, int]: (response_dict, status_code)
            - response_dict: JSON response with status and message
            - status_code: 200 (ACK message) or 400/500 (NACK message)
    
    Important:
        - Return HTTP 200 to ACK the message (message will NOT be redelivered)
        - Return any other status to NACK the message (Pub/Sub will retry)
    """
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    try:
        # Validate request exists
        if not request:
            error_msg = "No request provided"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "timestamp": timestamp
            }, 400
        
        # Get JSON body from request
        request_json = request.get_json()
        if not request_json:
            error_msg = "Request body is not JSON"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "timestamp": timestamp
            }, 400
        
        logger.info(f"Received Pub/Sub push request | MessageID: {request_json.get('message', {}).get('messageId', 'unknown')}")
        
        # Extract Pub/Sub message from envelope
        if 'message' not in request_json:
            error_msg = "Invalid Pub/Sub message format - missing 'message' field"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "timestamp": timestamp
            }, 400
        
        message = request_json['message']
        
        # Extract and validate required fields
        message_id = message.get('messageId', 'unknown')
        publish_time = message.get('publishTime', 'unknown')
        
        # Decode base64 message data
        if 'data' not in message:
            error_msg = "Invalid message format - missing 'data' field"
            logger.error(f"MessageID: {message_id} | {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "timestamp": timestamp
            }, 400
        
        try:
            message_data_b64 = message['data']
            message_data_bytes = base64.b64decode(message_data_b64)
            message_data_str = message_data_bytes.decode('utf-8')
            
            # Parse JSON message content
            gold_price_data = json.loads(message_data_str)
            
            logger.info(
                f"MessageID: {message_id} | "
                f"Symbol: {gold_price_data.get('symbol', 'N/A')} | "
                f"Price: {gold_price_data.get('price', 'N/A')} | "
                f"Updated: {gold_price_data.get('updatedAt', 'N/A')}"
            )
            
            # TODO: In production, implement actual processing logic here
            # For now, just logging the received message
            logger.info(
                f"MessageID: {message_id} | "
                f"Successfully processed gold price message"
            )
            
            # Return 200 OK to ACK the message
            response = {
                "status": "success",
                "message": "Gold price message received and processed successfully",
                "timestamp": timestamp,
                "messageId": message_id,
                "data": {
                    "symbol": gold_price_data.get('symbol'),
                    "price": gold_price_data.get('price'),
                    "updatedAt": gold_price_data.get('updatedAt')
                }
            }
            
            logger.info(f"MessageID: {message_id} | Processing completed - ACK sent")
            return response, 200
            
        except base64.binascii.Error as e:
            error_msg = f"Failed to decode base64 message data"
            logger.error(f"MessageID: {message_id} | {error_msg}: {str(e)}")
            return {
                "status": "error",
                "message": error_msg,
                "timestamp": timestamp,
                "messageId": message_id
            }, 400
        
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse message JSON"
            logger.error(f"MessageID: {message_id} | {error_msg}: {str(e)}")
            return {
                "status": "error",
                "message": error_msg,
                "timestamp": timestamp,
                "messageId": message_id
            }, 400
    
    except Exception as e:
        error_timestamp = datetime.now(timezone.utc).isoformat()
        error_msg = f"Unexpected error processing Pub/Sub message"
        logger.error(f"{error_msg}: {str(e)}", exc_info=True)
        
        return {
            "status": "error",
            "message": error_msg,
            "timestamp": error_timestamp,
            "error_detail": str(e)
        }, 500


if __name__ == "__main__":
    # For local testing with mock Pub/Sub push request
    print("Testing subscriber function with mock Pub/Sub push request...")
    
    import json
    import base64
    from unittest.mock import Mock
    
    # Create mock request
    mock_request = Mock()
    message_data = json.dumps({
        "name": "Gold",
        "price": 5196.30,
        "symbol": "XAU",
        "updatedAt": "2026-02-27T12:00:00+0700",
        "updatedAtReadable": "a few seconds ago"
    })
    
    mock_request.get_json.return_value = {
        "message": {
            "data": base64.b64encode(message_data.encode()).decode(),
            "messageId": "test-message-123",
            "publishTime": "2026-02-27T12:00:00.000Z",
            "attributes": {}
        },
        "subscription": "projects/gold-price-alert-488703/subscriptions/gold-price-alert-488703-topic-subscription"
    }
    
    response, status_code = receive_gold_price(mock_request)
    print(f"Status Code: {status_code}")
    print(f"Response: {json.dumps(response, indent=2)}")
