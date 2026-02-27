output "publisher_function_name" {
  description = "Name of the Publisher Cloud Function Gen 2"
  value       = google_cloudfunctions2_function.publisher_function.name
}

output "publisher_function_url" {
  description = "URI of the Publisher Cloud Function Gen 2"
  value       = google_cloudfunctions2_function.publisher_function.service_config[0].uri
}

output "subscriber_function_name" {
  description = "Name of the Subscriber Cloud Function Gen 2"
  value       = google_cloudfunctions2_function.subscriber_function.name
}

output "subscriber_function_url" {
  description = "URI of the Subscriber Cloud Function Gen 2"
  value       = google_cloudfunctions2_function.subscriber_function.service_config[0].uri
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

output "gcf_service_account_email" {
  description = "Service Account Email for Cloud Functions Gen 2"
  value       = google_service_account.gcf-sa.email
}

output "scheduler_service_account_email" {
  description = "Service Account Email for Cloud Scheduler"
  value       = google_service_account.scheduler_sa.email
}

output "deployment_info" {
  description = "Summary of the Cloud Functions Gen 2 deployment"
  value = {
    project_id          = var.project_id
    region              = var.region
    publisher_function  = google_cloudfunctions2_function.publisher_function.name
    subscriber_function = google_cloudfunctions2_function.subscriber_function.name
    publisher_url       = google_cloudfunctions2_function.publisher_function.service_config[0].uri
    subscriber_trigger  = "Pub/Sub via Eventarc"
    scheduler_trigger   = "Every 15 minutes (Asia/Jakarta)"
    cloud_functions_gen = "Gen 2"
  }
}
