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

