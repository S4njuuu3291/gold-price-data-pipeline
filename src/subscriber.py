from google.cloud import pubsub_v1
from src.utils import PROJECT_ID, TOPIC_ID
import logging 
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def subscribe_to_pubsub(project_id, topic_id):
    subscriber = pubsub_v1.SubscriberClient()
    topic_path = subscriber.topic_path(project_id, topic_id)
    subscription_path = subscriber.subscription_path(project_id, f"{topic_id}-subscription")

    # Push mode subscription
    try:
        if not subscriber.subscription_exists(subscription_path):
            subscriber.create_subscription(name=subscription_path, topic=topic_path)
            logger.info(f"Created subscription: {subscription_path}")
        else:
            logger.info(f"Subscription already exists: {subscription_path}")
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        return
    
    def callback(message):
        logger.info(f"Received message: {message.data.decode('utf-8')}")
        message.ack()

    # push mode
    

if __name__ == "__main__":
    subscribe_to_pubsub(PROJECT_ID, TOPIC_ID)
