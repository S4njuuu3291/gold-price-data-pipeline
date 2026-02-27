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
    
    Supports TWO trigger formats:
    
    1. Eventarc CloudEvents (Gen 2, native Pub/Sub):
       ce_specversion: 1.0
       ce_type: google.cloud.pubsub.topic.v1.messagePublished
       ce_source: projects/PROJECT_ID/topics/TOPIC_NAME
       ce_id, ce_time: metadata
       Body: JSON with message.data (base64)
    
    2. Pub/Sub PUSH envelope (legacy):
       {
           "message": {
               "data": "base64-encoded",
               "messageId": "...",
               "publishTime": "...",
               "attributes": {}
           },
           "subscription": "..."
       }
    
    Args:
        request: Flask request object from Cloud Function environment.
    
    Returns:
        Tuple[Dict, int]: (response_dict, status_code) - 200 to ACK
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
        
        # Detect format: CloudEvents or Pub/Sub push envelope
        message_id = None
        message_data_b64 = None
        
        # Check if this is CloudEvents (Eventarc Gen 2)
        if 'message' in request_json and isinstance(request_json['message'], dict) and 'data' in request_json['message']:
            # Legacy Pub/Sub PUSH envelope format
            logger.info("Processing Pub/Sub PUSH envelope format")
            message = request_json['message']
            message_id = message.get('messageId', 'unknown')
            message_data_b64 = message.get('data')
            
            if not message_data_b64:
                error_msg = "Invalid message format - missing 'data' field"
                logger.error(f"MessageID: {message_id} | {error_msg}")
                return {
                    "status": "error",
                    "message": error_msg,
                    "timestamp": timestamp
                }, 400
        
        else:
            # CloudEvents format (Eventarc)
            logger.info("Processing CloudEvents format (Eventarc)")
            
            # Extract from headers
            message_id = request.headers.get('ce_id', 'unknown')
            ce_type = request.headers.get('ce_type', '')
            
            # Extract base64 data from CloudEvents body
            if isinstance(request_json, dict) and 'message' in request_json:
                message = request_json.get('message', {})
                message_data_b64 = message.get('data')
            else:
                message_data_b64 = None
            
            if not message_data_b64:
                error_msg = "Invalid CloudEvents format - missing message.data"
                logger.error(f"MessageID: {message_id} | {error_msg}")
                return {
                    "status": "error",
                    "message": error_msg,
                    "timestamp": timestamp
                }, 400
        
        # Validate and decode base64 data
        try:
            if not message_data_b64:
                raise ValueError("No message data to decode")
                
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
