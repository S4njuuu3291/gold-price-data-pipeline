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
    "iam.googleapis.com",
    "artifactregistry.googleapis.com",
    "eventarc.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com"
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

  depends_on = [google_project_service.required_apis]
}

# ========================================================
# Google Cloud Function Bucket Source Code (Gen 2)
# ========================================================
resource "google_storage_bucket" "gcf_source_bucket" {
  name          = "${var.project_id}-gcf-source"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  depends_on = [google_project_service.required_apis]
}

# ========================================================
# Artifact Registry Repository for Cloud Functions Gen 2
# ========================================================
resource "google_artifact_registry_repository" "cloud_functions_repo" {
  location      = var.region
  repository_id = "cloud-functions"
  description   = "Docker repository for Cloud Functions Gen 2"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}

# ========================================================
# Service Accounts and IAM Roles
# ========================================================

# Service Account for Cloud Functions
resource "google_service_account" "gcf-sa" {
  account_id   = "${var.project_id}-gcf-sa"
  display_name = "Service Account for Cloud Functions Gen 2"
}

# IAM: Grant Read/Write access to the bucket for the service account
resource "google_storage_bucket_iam_member" "bucket_access" {
  bucket = google_storage_bucket.gold_price_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.gcf-sa.email}"
}

# IAM: Grant Secret Manager access to the service account
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

# IAM: Grant Eventarc Event Receiver role for Pub/Sub triggers
resource "google_project_iam_member" "gcf_eventarc_receiver" {
  project = var.project_id
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${google_service_account.gcf-sa.email}"

  depends_on = [google_service_account.gcf-sa]
}

# ========================================================
# Cloud Function Gen 2: Publisher (HTTP Trigger)
# ========================================================

# Create ZIP archive for publisher source code
data "archive_file" "publisher_source" {
  type        = "zip"
  output_path = "/tmp/publisher-source.zip"
  source_dir  = "${path.module}/../src/publisher"

  depends_on = [google_project_service.required_apis]
}

# Upload publisher source code to GCS
resource "google_storage_bucket_object" "publisher_source" {
  name   = "publisher-source-${data.archive_file.publisher_source.output_base64sha256}.zip"
  bucket = google_storage_bucket.gcf_source_bucket.name
  source = data.archive_file.publisher_source.output_path

  depends_on = [data.archive_file.publisher_source]
}

# Deploy Publisher Cloud Function Gen 2
resource "google_cloudfunctions2_function" "publisher_function" {
  name        = "${var.project_id}-publisher"
  location    = var.region
  description = "Gold price publisher function - triggered by Cloud Scheduler"

  build_config {
    runtime     = "python313"
    entry_point = "publish_gold_price"

    source {
      storage_source {
        bucket = google_storage_bucket.gcf_source_bucket.name
        object = google_storage_bucket_object.publisher_source.name
      }
    }

    docker_repository = "projects/${var.project_id}/locations/${var.region}/repositories/cloud-functions"
  }

  service_config {
    max_instance_count               = 10
    timeout_seconds                  = 60
    max_instance_request_concurrency = 1
    min_instance_count               = 0

    environment_variables = {
      PROJECT_ID = var.project_id
      TOPIC_ID   = google_pubsub_topic.gold_price_topic.name
    }

    service_account_email = google_service_account.gcf-sa.email
    ingress_settings      = "ALLOW_ALL"
  }

  depends_on = [
    google_storage_bucket_object.publisher_source,
    google_project_iam_member.gcf_pubsub_publisher,
    google_project_iam_member.gcf_logging_writer,
    google_artifact_registry_repository.cloud_functions_repo,
    google_project_service.required_apis
  ]

  labels = {
    environment = var.environment
    project     = var.project_name
  }
}

# ========================================================
# Cloud Function Gen 2: Subscriber (Pub/Sub Trigger via Eventarc)
# ========================================================

# Create ZIP archive for subscriber source code
data "archive_file" "subscriber_source" {
  type        = "zip"
  output_path = "/tmp/subscriber-source.zip"
  source_dir  = "${path.module}/../src/subscriber"

  depends_on = [google_project_service.required_apis]
}

# Upload subscriber source code to GCS
resource "google_storage_bucket_object" "subscriber_source" {
  name   = "subscriber-source-${data.archive_file.subscriber_source.output_base64sha256}.zip"
  bucket = google_storage_bucket.gcf_source_bucket.name
  source = data.archive_file.subscriber_source.output_path

  depends_on = [data.archive_file.subscriber_source]
}

# Deploy Subscriber Cloud Function Gen 2 with Pub/Sub Eventarc Trigger
resource "google_cloudfunctions2_function" "subscriber_function" {
  name        = "${var.project_id}-subscriber"
  location    = var.region
  description = "Gold price subscriber function - triggered by Pub/Sub via Eventarc"

  build_config {
    runtime     = "python313"
    entry_point = "receive_gold_price"

    source {
      storage_source {
        bucket = google_storage_bucket.gcf_source_bucket.name
        object = google_storage_bucket_object.subscriber_source.name
      }
    }

    docker_repository = "projects/${var.project_id}/locations/${var.region}/repositories/cloud-functions"
  }

  service_config {
    max_instance_count               = 10
    timeout_seconds                  = 60
    max_instance_request_concurrency = 1
    min_instance_count               = 0

    environment_variables = {
      PROJECT_ID = var.project_id
    }

    service_account_email = google_service_account.gcf-sa.email
    ingress_settings      = "ALLOW_ALL"
  }

  event_trigger {
    trigger_region        = var.region
    event_type            = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic          = google_pubsub_topic.gold_price_topic.id
    service_account_email = google_service_account.gcf-sa.email
  }

  depends_on = [
    google_storage_bucket_object.subscriber_source,
    google_project_iam_member.gcf_logging_writer,
    google_project_iam_member.gcf_eventarc_receiver,
    google_artifact_registry_repository.cloud_functions_repo,
    google_project_service.required_apis
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

# IAM: Grant Cloud Functions Invoker role to Cloud Scheduler (Gen 2 requires Run Invoker)
resource "google_project_iam_member" "scheduler_invoke_cf" {
  project = var.project_id
  role    = "roles/cloudfunctions.invoker"
  member  = "serviceAccount:${google_service_account.scheduler_sa.email}"

  depends_on = [google_service_account.scheduler_sa]
}

# IAM: Grant Cloud Run Invoker role to Cloud Scheduler (required for Gen 2 functions)
resource "google_cloud_run_v2_service_iam_member" "scheduler_run_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloudfunctions2_function.publisher_function.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_sa.email}"

  depends_on = [
    google_cloudfunctions2_function.publisher_function,
    google_service_account.scheduler_sa
  ]
}

# Cloud Scheduler Job: Trigger Publisher every 15 minutes
resource "google_cloud_scheduler_job" "publisher_trigger" {
  name             = "${var.project_id}-publisher-scheduler"
  description      = "Trigger gold price publisher every 15 minutes"
  schedule         = "*/15 * * * *" # Every 15 minutes
  time_zone        = "Asia/Jakarta"
  attempt_deadline = "320s"
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.publisher_function.service_config[0].uri

    oidc_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }

  depends_on = [
    google_cloudfunctions2_function.publisher_function,
    google_project_iam_member.scheduler_invoke_cf
  ]
}

# ========================================================
# Pub/Sub Subscription for DLQ and Manual Monitoring
# ========================================================

# Note: For Gen 2 Subscriber, the Eventarc trigger handles message delivery natively
# This subscription is optional for:
# - Dead Letter Queue (DLQ) policy
# - Manual message inspection
# - Monitoring and debugging
resource "google_pubsub_subscription" "gold_price_subscription" {
  name  = "${var.project_id}-subscription"
  topic = google_pubsub_topic.gold_price_topic.name

  # Message acknowledgement settings
  ack_deadline_seconds = 60

  # Dead letter queue for failed messages
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.gold_price_dlq_topic.id
    max_delivery_attempts = 5
  }

  # Message retention - 24 hours
  message_retention_duration = "86400s"

  depends_on = [
    google_pubsub_topic.gold_price_dlq_topic,
    google_project_service.required_apis
  ]

  labels = {
    environment = var.environment
    project     = var.project_name
    type        = "dlq-subscription"
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

  depends_on = [google_project_service.required_apis]
}