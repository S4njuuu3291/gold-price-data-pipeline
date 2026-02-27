terraform {
  backend "gcs" {
    bucket = "gold-price-tfstate-sanju"
    prefix = "terraform/state"
  }
}

# ========================================================
# Enable Required APIs
# ========================================================
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com"
  ])

  project = var.project_id
  service = each.value

  disable_on_destroy = false
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "gold_price_bucket" {
  name     = "${var.project_id}-bucket"
  location = var.region

  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_topic" "gold_price_topic" {
  name = "${var.project_id}-topic"

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# ========================================================
# Google Cloud Function Bucket Source Code
# ========================================================
resource "google_storage_bucket" "gcf_source_bucket" {
  name          = "${var.project_id}-gcf-source"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
}

# ========================================================
# Cloud Function to fetch gold price and publish to Pub/Sub
# ========================================================

# Service Account untuk Cloud Function
resource "google_service_account" "gcf-sa" {
  account_id   = "${var.project_id}-gcf-sa"
  display_name = "Service Account for Cloud Function"
}

# IAM: Grant Read/Write access to the bucket for the service account
resource "google_storage_bucket_iam_member" "bucket_access" {
  bucket = google_storage_bucket.gold_price_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.gcf-sa.email}"
}

# IAM: Grant Secret manager access to the service account
resource "google_project_iam_member" "gcf_secret_access" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.gcf-sa.email}"

  depends_on = [
    google_service_account.gcf-sa,
    google_project_service.required_apis
  ]
}

# IAM: Grant Pub/Sub Publisher role to allow publishing messages
resource "google_project_iam_member" "gcf_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.gcf-sa.email}"

  depends_on = [google_service_account.gcf-sa]
}

# IAM: Grant Cloud Logging Writer role for Cloud Function logging
resource "google_project_iam_member" "gcf_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gcf-sa.email}"

  depends_on = [google_service_account.gcf-sa]
}

# ========================================================
# Cloud Function: Publisher (Fetch and Publish Gold Price)
# ========================================================

# Create ZIP archive for publisher source code
data "archive_file" "publisher_source" {
  type        = "zip"
  output_path = "/tmp/publisher-source.zip"
  source_dir  = "${path.module}/../src/publisher"

  depends_on = [
    google_project_service.required_apis
  ]
}

# Upload publisher source code to GCS
resource "google_storage_bucket_object" "publisher_source" {
  name   = "publisher-source-${data.archive_file.publisher_source.output_base64sha256}.zip"
  bucket = google_storage_bucket.gcf_source_bucket.name
  source = data.archive_file.publisher_source.output_path

  depends_on = [data.archive_file.publisher_source]
}

# Deploy Publisher Cloud Function
resource "google_cloudfunctions_function" "publisher_function" {
  name                = "${var.project_id}-publisher"
  runtime             = "python313"
  available_memory_mb = 512
  timeout             = 60

  source_archive_bucket = google_storage_bucket.gcf_source_bucket.name
  source_archive_object = google_storage_bucket_object.publisher_source.name

  entry_point = "publish_gold_price"

  environment_variables = {
    PROJECT_ID = var.project_id
    TOPIC_ID   = google_pubsub_topic.gold_price_topic.name
  }

  service_account_email = google_service_account.gcf-sa.email

  ingress_settings = "ALLOW_ALL"

  depends_on = [
    google_storage_bucket_object.publisher_source,
    google_project_iam_member.gcf_pubsub_publisher,
    google_project_iam_member.gcf_logging_writer
  ]

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# ========================================================
# Cloud Function: Subscriber (Receive and Process Messages)
# ========================================================

# Create ZIP archive for subscriber source code
data "archive_file" "subscriber_source" {
  type        = "zip"
  output_path = "/tmp/subscriber-source.zip"
  source_dir  = "${path.module}/../src/subscriber"

  depends_on = [
    google_project_service.required_apis
  ]
}

# Upload subscriber source code to GCS
resource "google_storage_bucket_object" "subscriber_source" {
  name   = "subscriber-source-${data.archive_file.subscriber_source.output_base64sha256}.zip"
  bucket = google_storage_bucket.gcf_source_bucket.name
  source = data.archive_file.subscriber_source.output_path

  depends_on = [data.archive_file.subscriber_source]
}

# Deploy Subscriber Cloud Function
resource "google_cloudfunctions_function" "subscriber_function" {
  name                = "${var.project_id}-subscriber"
  runtime             = "python313"
  available_memory_mb = 512
  timeout             = 60

  source_archive_bucket = google_storage_bucket.gcf_source_bucket.name
  source_archive_object = google_storage_bucket_object.subscriber_source.name

  entry_point = "receive_gold_price"

  environment_variables = {
    PROJECT_ID = var.project_id
  }

  service_account_email = google_service_account.gcf-sa.email

  ingress_settings = "ALLOW_ALL"

  depends_on = [
    google_storage_bucket_object.subscriber_source,
    google_project_iam_member.gcf_logging_writer
  ]

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# ========================================================
# Cloud Scheduler: Trigger Publisher Cloud Function every 15 minutes
# ========================================================

# Service Account for Cloud Scheduler
resource "google_service_account" "scheduler_sa" {
  account_id   = "gold-price-sched-sa"
  display_name = "Service Account for Cloud Scheduler"
}

# IAM: Grant Cloud Scheduler to invoke Cloud Functions
resource "google_project_iam_member" "scheduler_invoke_cf" {
  project = var.project_id
  role    = "roles/cloudfunctions.invoker"
  member  = "serviceAccount:${google_service_account.scheduler_sa.email}"

  depends_on = [google_service_account.scheduler_sa]
}

# Cloud Scheduler Job: Trigger Publisher every 15 minutes
resource "google_cloud_scheduler_job" "publisher_trigger" {
  name             = "${var.project_id}-publisher-scheduler"
  description      = "Trigger gold price publisher every 15 minutes"
  schedule         = "*/15 * * * *" # Every 15 minutes
  time_zone        = "Asia/Jakarta"
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions_function.publisher_function.https_trigger_url

    oidc_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }

  depends_on = [
    google_cloudfunctions_function.publisher_function,
    google_project_iam_member.scheduler_invoke_cf
  ]
}

# ========================================================
# Pub/Sub Subscription: Push mode to Subscriber Cloud Function
# ========================================================

# Pub/Sub Push Subscription
resource "google_pubsub_subscription" "gold_price_subscription" {
  name  = "${var.project_id}-subscription"
  topic = google_pubsub_topic.gold_price_topic.name

  # Push configuration - delivers messages via HTTP POST to the subscriber function
  push_config {
    push_endpoint = google_cloudfunctions_function.subscriber_function.https_trigger_url

    # Authenticate the push request with OIDC token
    oidc_token {
      service_account_email = google_service_account.gcf-sa.email
    }
  }

  # Message acknowledgement settings
  ack_deadline_seconds = 60

  # Dead letter queue for failed messages
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.gold_price_dlq_topic.id
    max_delivery_attempts = 5
  }

  # Message retention
  message_retention_duration = "86400s" # 24 hours

  depends_on = [
    google_cloudfunctions_function.subscriber_function,
    google_pubsub_topic.gold_price_dlq_topic
  ]

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# ========================================================
# Pub/Sub Dead Letter Queue Topic
# ========================================================
resource "google_pubsub_topic" "gold_price_dlq_topic" {
  name = "${var.project_id}-dlq-topic"

  labels = {
    environment = var.environment
    project     = var.project_name
    purpose     = "dead-letter-queue"
  }
}