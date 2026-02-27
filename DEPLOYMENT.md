# Gold Price Data Pipeline - Deployment & Architecture Guide

## 📊 Architecture Overview

The system implements a **fully automated ETL pipeline** using Google Cloud Platform services:

```
+─────────────────┐
│ Cloud Scheduler │ (Every 15 minutes)
│  (Cron: */15)   │
└────────┬────────┘
         │ HTTP POST
         ▼
+─────────────────────────────────┐
│  Publisher Cloud Function       │
│  - Fetch gold price (API)       │
│  - Validate data (Pydantic)     │
│  - Publish to Pub/Sub Topic     │
└────────┬────────────────────────┘
         │ Pub/Sub Message
         ▼
+─────────────────────────────────┐
│     Pub/Sub Topic                │
│ (gold-price-alert-488703-topic) │
└────────┬────────────────────────┘
         │ Push Subscription
         ▼
+─────────────────────────────────┐
│  Subscriber Cloud Function      │
│  - Receive message (HTTPS push) │
│  - Decode Base64 data           │
│  - Process/Log message          │
│  - ACK (HTTP 200)               │
└────────┬────────────────────────┘
         │ Failed messages
         ▼
      DLQ Topic
```

## 🚀 Deployment Steps

### Prerequisites
- GCP Project with APIs enabled (automatic via Terraform)
- Service Account Key (stored in GitHub Secrets as `GCP_SA_KEY`)
- Terraform >= 1.0
- Poetry >= 1.8.0

### Step 1: Local Testing (Optional)

Run unit tests locally:
```bash
poetry install --no-root
poetry run pytest test/ -v
```

Validate Terraform:
```bash
cd terraform
terraform init
terraform validate
terraform plan
```

### Step 2: Deploy via CI/CD (Recommended)

Push changes to `dev` or `setup/**` branch:

```bash
git add .
git commit -m "Deploy publisher and subscriber"
git push origin setup/infra-as-code-cicd
```

The GitHub Actions workflow will:
1. ✅ Run all unit tests (27 tests)
2. ✅ Validate Terraform syntax
3. ✅ Generate Terraform plan
4. ✅ Apply Terraform (create all resources)
5. ✅ Output deployment information

## 📁 Project Structure

```
gold-price-data-pipeline/
├── src/
│   ├── publisher/
│   │   ├── __init__.py
│   │   ├── main.py           # Publisher Cloud Function entry point
│   │   ├── publisher.py      # Pub/Sub publishing logic
│   │   └── fetcher.py        # Gold price fetching with Pydantic & Tenacity
│   ├── subscriber/
│   │   ├── __init__.py
│   │   └── main.py           # Subscriber Cloud Function entry point
│   ├── subscriber.py         # Legacy subscriber (keep for reference)
│   └── utils.py              # Shared utilities and secrets
├── test/
│   ├── test_fetcher.py       # 7 tests for fetcher
│   ├── test_main.py          # 5 tests for publisher CF
│   ├── test_publisher.py     # 3 tests for Pub/Sub
│   └── test_subscriber.py    # 12 tests for subscriber CF
├── terraform/
│   ├── main.tf               # Infrastructure resources
│   ├── variables.tf          # Variable definitions
│   ├── outputs.tf            # Output values
│   ├── versions.tf           # Provider versions
│   └── terraform.tfvars      # (Generated during CI/CD)
└── .github/workflows/
    └── ci-cd.yml             # GitHub Actions CI/CD pipeline
```

## 🔧 Configuration

### Publisher Cloud Function

**Trigger:** Cloud Scheduler (every 15 minutes, 02:00 JST/WIB timezone)

**Environment Variables:**
- `PROJECT_ID`: GCP project ID
- `TOPIC_ID`: Pub/Sub topic name

**Features:**
- Fetches gold price from external API (URL from Secret Manager)
- Validates data with Pydantic model
- Retries up to 3 times with exponential backoff (tenacity)
- Converts timestamp UTC → WIB (UTC+7)
- Publishes JSON message to Pub/Sub

### Subscriber Cloud Function

**Trigger:** Pub/Sub push subscription (automatic when message published)

**Authentication:** OIDC token (Service Account)

**Features:**
- Receives HTTP POST from Pub/Sub with push envelope
- Decodes base64-encoded message data
- Validates JSON structure
- Logs message details (symbol, price, timestamp)
- Returns HTTP 200 to ACK (prevents redelivery)
- Returns HTTP 400/500 to NACK (triggers retry)

## 📊 Data Model

### Gold Price Message

```json
{
  "name": "Gold",
  "price": 5196.299805,
  "symbol": "XAU",
  "updatedAt": "2026-02-27T13:09:24+0700",
  "updatedAtReadable": "a few seconds ago"
}
```

**Validated by Pydantic with:**
- `price` must be positive number
- `symbol` must not be empty
- All fields required

## 🧪 Testing

### Test Coverage: 27 tests

**Fetcher Tests (7):**
- Successful fetch with API
- API URL retrieval failures
- Network exception handling
- Data validation (positive price, non-empty symbol)
- Timezone conversion (UTC to WIB)

**Publisher Function Tests (5):**
- Successful publish flow
- Fetch failures
- Publishing exceptions
- Response format validation
- Error handling

**Pub/Sub Tests (3):**
- Successful publish to topic
- Different data types
- Exception handling

**Subscriber Function Tests (12):**
- Successful message processing
- Invalid request formats
- Base64 decoding errors
- JSON parsing errors
- Message ID handling
- UTF-8 character support

Run tests:
```bash
poetry run pytest test/ -v
```

## 🔍 Monitoring & Logging

### Cloud Logging
View logs for both functions:
```bash
gcloud functions logs read gold-price-alert-488703-publisher --limit 50
gcloud functions logs read gold-price-alert-488703-subscriber --limit 50
```

### Cloud Scheduler
Monitor scheduler execution:
```bash
gcloud scheduler jobs list
gcloud scheduler jobs describe gold-price-alert-488703-publisher-scheduler
```

### Pub/Sub
Monitor topic and subscription:
```bash
gcloud pubsub topics list
gcloud pubsub subscriptions list
```

## 🛠️ Troubleshooting

### Publisher Function Not Executing

Check Cloud Scheduler job:
```bash
gcloud scheduler jobs describe gold-price-alert-488703-publisher-scheduler
```

Verify service account permissions:
```bash
gcloud projects get-iam-policy gold-price-alert-488703 \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/cloudfunctions.invoker"
```

### Subscriber Not Receiving Messages

Check subscription configuration:
```bash
gcloud pubsub subscriptions describe gold-price-alert-488703-subscription
```

Verify push endpoint is reachable:
```bash
curl -X POST \
  https://<region>-<project>.cloudfunctions.net/gold-price-alert-488703-subscriber \
  -H "Content-Type: application/json" \
  -d '{"message": {"data": "test"}}'
```

### Message Delivery Failed

Check Dead Letter Queue:
```bash
gcloud pubsub topics list-subscriptions gold-price-alert-488703-dlq-topic
```

## 📈 Performance Tuning

### Cloud Functions Configuration

**Current Settings:**
- Memory: 512 MB
- Timeout: 60 seconds
- Concurrency: Auto (Google managed)

Adjust if needed in `terraform/main.tf`:
```tf
available_memory_mb = 512  # Increase for slower processing
timeout            = 60    # Increase for longer operations
```

### Pub/Sub Configuration

**Current Settings:**
- ACK deadline: 60 seconds
- Message retention: 24 hours
- Max delivery attempts: 5

Adjust in `terraform/main.tf`:
```tf
ack_deadline_seconds       = 60
message_retention_duration = "86400s"  # 24 hours
max_delivery_attempts      = 5
```

## 🔐 Security

### Service Accounts

**GCF Service Account:**
- Read: Secret Manager (gold price API URL)
- Write: Pub/Sub (publish messages)
- Write: Cloud Logging (log output)
- Read: GCS (access source code)

**Scheduler Service Account:**
- Invoke: Cloud Functions (trigger publisher)

### Secrets

Gold price API URL stored in Secret Manager:
- Secret name: `GOLD_API_KEY`
- Accessed via: `get_secret_value()` function

## 📝 Next Steps (Future Enhancements)

1. **Data Persistence:** Store gold prices in BigQuery/Cloud SQL
2. **Alerting:** Send email/Slack when price exceeds threshold
3. **Dashboard:** CloudSQL data → Looker dashboard
4. **API Gateway:** Expose REST API for price queries
5. **Authentication:** Add API key validation for subscribers
6. **Multi-Region:** Deploy to multiple regions for redundancy
7. **Cost Optimization:** Implement Cloud Workflow instead of Scheduler+CF

## 📞 Support

For issues or questions:
1. Check Cloud Logging for error messages
2. Review test results in GitHub Actions
3. Validate Terraform plan before applying
4. Monitor service account permissions

---

**Last Updated:** 2026-02-27
**Version:** 1.0.0
