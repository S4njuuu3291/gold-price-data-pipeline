# Gold Price Data Pipeline

A data pipeline project that fetches real-time gold prices from an API and sends notifications to Slack.

## Project Overview

This project is designed to:
- Fetch current gold prices from the Gold API
- Format the price data with timestamps
- Send notifications to Slack with the latest gold price information

## Features

- **Real-time Gold Price Fetching**: Retrieves current gold prices in USD for XAU (Gold) symbol
- **Slack Integration**: Sends formatted price notifications to a Slack channel via webhook
- **Environment Configuration**: Supports environment variables for secure credential management
- **Error Handling**: Handles API failures and HTTP errors gracefully

## Requirements

- Python >= 3.13
- Dependencies:
  - beautifulsoup4 (>=4.14.3, <5.0.0)
  - pywhatkit (>=5.4, <6.0)
  - python-dotenv (>=0.9.9, <0.10.0)

## Installation

### Prerequisites
- Python 3.13 or higher
- Virtual environment (recommended)

### Setup

1. Clone or navigate to the project directory:
```bash
cd gold-price-data-pipeline
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # On Windows PowerShell
source .venv/bin/activate   # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file in the project root directory:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

To get your Slack Webhook URL:
1. Go to your Slack workspace settings
2. Create an Incoming Webhook to your desired channel
3. Copy the webhook URL and add it to your `.env` file

## Usage

Run the script to fetch the gold price and send it to Slack:

```bash
python slack.py
```

### Example Output

The script will send a message to Slack in the format:
```
Harga emas saat ini adalah 5178.40 USD per XAU (update: 2026-02-27T02:56:24Z)
```

## API Reference

### Gold API
- **Endpoint**: `https://api.gold-api.com/price/XAU`
- **Method**: GET
- **Response Format**:
```json
{
  "name": "Gold",
  "price": 5178.399902,
  "symbol": "XAU",
  "updatedAt": "2026-02-27T02:56:24Z",
  "updatedAtReadable": "a few seconds ago"
}
```

## File Structure

```
gold-price-data-pipeline/
├── slack.py              # Main script for fetching gold prices and sending Slack notifications
├── pyproject.toml        # Project metadata and dependencies
├── README.md             # This file
├── TDD.md               # Test-Driven Development notes
├── img/                 # Images/assets directory
└── .venv/               # Virtual environment (local)
```

## Functions

### `get_gold_price()`
Fetches the current gold price from the Gold API and formats it.

**Returns**: Formatted string with gold price in Indonesian, or None if request fails

### `send_slack_notification(message)`
Sends a message to Slack via webhook.

**Parameters**:
- `message` (str): The message to send to Slack

## Error Handling

The script includes error handling for:
- Failed API requests (non-200 status codes)
- Failed Slack webhook notifications
- Missing or invalid environment variables

## Author

**S4njuuu3291** - sanju329121@gmail.com