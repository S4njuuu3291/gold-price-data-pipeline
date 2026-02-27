# GitHub Secrets Configuration Guide

## Required Secrets for CI/CD Pipeline

Add these secrets to your GitHub repository under Settings → Secrets and variables → Actions:

### 1. GCP_SA_KEY (Required)
- **Purpose**: Google Cloud Service Account JSON credentials for Terraform deployment
- **How to get it**:
  1. Go to Google Cloud Console → Service Accounts
  2. Create or select existing service account
  3. Create a new JSON key
  4. Copy the entire JSON content
  5. Add as GitHub secret named `GCP_SA_KEY`
- **Permissions needed**: 
  - Compute Admin
  - Pub/Sub Admin
  - Storage Admin

### 2. GCP_PROJECT_ID (Required)
- **Purpose**: Your GCP Project ID
- **Example**: `gold-price-alert-488703`

## Environment Configuration

The workflow uses GitHub Environments to manage secrets per environment:
- **dev**: Development environment (terraform apply runs on push to `dev` branch)

### Setting up Environment Secrets:
1. Go to Settings → Environments
2. Create `dev` environment if not exists
3. Add secrets specific to this environment:
   - `GCP_SA_KEY`
   - `GCP_PROJECT_ID`

## Terraform Variables

The following variables are automatically set by the GitHub Actions workflow:

```
TF_VAR_project_id     = GCP_PROJECT_ID (from secrets)
TF_VAR_project_name   = "gold-price-alert"
TF_VAR_region         = "asia-southeast2"
TF_VAR_environment    = "dev"
```

These correspond to variables in `terraform/variables.tf`:
- `project_name`: Name of the GCP project
- `project_id`: GCP Project ID
- `region`: GCP region for resources
- `environment`: Deployment environment (dev/staging/prod)

## Workflow Triggers

- **Push to `dev` branch**: Runs terraform plan + apply
- **Push to `setup/**` branches**: Runs terraform plan only (no apply)
- **Pull Requests to `main`**: Runs terraform plan only
- **Manual trigger**: Use workflow_dispatch from Actions tab

## Troubleshooting

### "the GitHub Action workflow must specify exactly one of workload_identity_provider or credentials_json"
- **Cause**: `GCP_SA_KEY` secret is not set or not accessible to the workflow
- **Solution**: 
  1. Check if secret exists in repository/environment settings
  2. For forks/PRs from forks: Secrets are not available by default. Enable "Run workflows from fork pull requests" in Actions settings
  3. Ensure secret is set in the correct environment (`dev`)

### "Permission denied" errors
- **Cause**: Service account doesn't have required permissions
- **Solution**: 
  1. Check service account has: Compute Admin, Pub/Sub Admin, Storage Admin roles
  2. Re-create or download the service account key
  3. Update `GCP_SA_KEY` secret with new key

### Terraform variables not being used
- **Cause**: Environment variables not properly set
- **Solution**: Check `env` section in workflow and ensure secret names match
