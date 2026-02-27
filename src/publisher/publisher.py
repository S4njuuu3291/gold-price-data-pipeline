import logging
import google.cloud.pubsub_v1 as pubsub

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def publish_to_pubsub(project_id, topic_id, data):
    publisher = pubsub.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    try:
        future = publisher.publish(topic_path, data.encode("utf-8"))
        future.result()  # Wait for the publish to complete
        logger.info(f"Published message to {topic_path}")
    except Exception as e:
        logger.error(f"Failed to publish message: {e}")