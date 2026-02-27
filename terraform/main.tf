provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "gold_price_bucket" {
  name     = "${var.project_id}-bucket"
  location = var.region

  force_destroy = true

  uniform_bucket_level_access = true
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
    name     = "${var.project_id}-gcf-source"
    location = var.region
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

  depends_on = [google_service_account.gcf-sa]
}