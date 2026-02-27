output "publisher_function_name" {
  description = "Name of the Publisher Cloud Function"
  value       = google_cloudfunctions_function.publisher_function.name
}

output "publisher_function_url" {
  description = "HTTPS trigger URL for the Publisher Cloud Function"
  value       = google_cloudfunctions_function.publisher_function.https_trigger_url
}

output "subscriber_function_name" {
  description = "Name of the Subscriber Cloud Function"
  value       = google_cloudfunctions_function.subscriber_function.name
}

output "subscriber_function_url" {
  description = "HTTPS trigger URL for the Subscriber Cloud Function"
  value       = google_cloudfunctions_function.subscriber_function.https_trigger_url
}

output "cloud_scheduler_job_name" {
  description = "Cloud Scheduler Job Name"
  value       = google_cloud_scheduler_job.publisher_trigger.name
}

output "pubsub_topic_name" {
  description = "Pub/Sub Topic Name"
  value       = google_pubsub_topic.gold_price_topic.name
}

output "pubsub_subscription_name" {
  description = "Pub/Sub Subscription Name"
  value       = google_pubsub_subscription.gold_price_subscription.name
}

output "pubsub_dlq_topic_name" {
  description = "Pub/Sub Dead Letter Queue Topic Name"
  value       = google_pubsub_topic.gold_price_dlq_topic.name
}

output "service_account_email" {
  description = "Service Account Email for Cloud Functions"
  value       = google_service_account.gcf-sa.email
}

output "deployment_info" {
  description = "Summary of the deployment"
  value = {
    project_id  = var.project_id
    region      = var.region
    environment = var.environment
  }
}
