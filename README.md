# TaxBot

TaxBot is a Telegram bot for processing and summarizing tax transaction data.
Users can request an Excel template, fill in their transaction details, and receive a summary of income totals in GEL.

## Features
- Send and receive an `.xlsx` template with predefined columns
- Fetch currency exchange rates from the Georgian National Bank API
- Calculate year-to-date totals and breakdown by income source
- Interactive Telegram conversation with buttons

## Requirements
- Python 3.8+
- `python-telegram-bot` library
- `pandas`, `requests`, `openpyxl` and other dependencies listed in `requirements.txt`

## Setup
1. Clone this repository:
   ```bash
   git clone https://github.com/religofsil/taxbot.git
   cd taxbot
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the project root with your Bot token:
   ```ini
   BOT_TOKEN=your-telegram-bot-token-here
   ```

## Running the Bot
Start the bot with:
```bash
python3 bot.py
```

In Telegram, send `/start` to your bot, click **Receive template**, fill the Excel file, and upload it. Then enter your previous period amount in GEL. The bot will reply with a summary of Fields 15, 18–21.

## Project Structure
```
bot.py              # Main Telegram bot handlers
requirements.txt    # Python dependencies
parse_tax_template.ipynb  # Notebook for local testing and data processing
README.md           # Project overview and instructions
.gitignore          # Ignored files and folders
```

## License
MIT © 2025
