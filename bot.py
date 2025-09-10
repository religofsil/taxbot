import asyncio
import os
from io import BytesIO
from datetime import datetime, date
from dotenv import load_dotenv
load_dotenv()
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

import pandas as pd
from telegram import Update, InputFile, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)
from requests import get

# States
AWAIT_SELECTION = 0
AWAIT_FILE = 1
AWAIT_PREV_AMOUNT = 2

ALLOWED_CURRENCIES = {"GEL", "EUR", "USD"}
ALLOWED_SOURCES = {
    "Bank transaction",
    "POS terminal payment",
    "Cash",
    "Payment system: PayPal, Wise, Deel, etc.",
}

FIELD_MAP = {
    15: ("gel_ytd", None),   # GEL total since Jan 1 this year to today (inclusive)
    18: ("source",  "Cash"),
    19: ("source",  "POS terminal payment"),
    20: ("source",  "Bank transaction"),
    21: ("source",  "Payment system: PayPal, Wise, Deel, etc."),
}

# ---------- Helpers ----------

def build_template_bytes() -> BytesIO:
    """
    Columns (exact order):
    Transaction amount, Currency, Transaction date, Income source
    """
    df = pd.DataFrame({
        "Transaction amount": [100.00],
        "Currency": ["GEL"],
        "Transaction date": [pd.Timestamp(date.today())],
        "Income source": ["Payment system: PayPal, Wise, Deel, etc."],
    })
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as xw:
        df.to_excel(xw, index=False, sheet_name="Data")
        ws = xw.sheets["Data"]
        ws.set_column("A:A", 22)
        ws.set_column("B:B", 10)
        ws.set_column("C:C", 16)
        ws.set_column("D:D", 40)
    bio.seek(0)
    return bio

def build_instructions() -> str:
    return (
        "Template rules:\n"
        "• Columns (order): Transaction amount, Currency, Transaction date, Income source\n"
        "• Currency: GEL, EUR, USD\n"
        "• Date: YYYY-MM-DD\n"
        "• Income source:\n"
        "  – Bank transaction\n"
        "  – POS terminal payment\n"
        "  – Cash\n"
        "  – Payment system: PayPal, Wise, Deel, etc.\n"
        "Send the filled .xlsx back here."
    )

def get_currency_rate(currency: str, on_date: date) -> float:
    """
    Get currency exchange rate from Georgian National Bank API.
    
    Args:
        currency (str): Currency code (e.g., 'USD', 'EUR')
        on_date (date): Date for which to get the exchange rate
        
    Returns:
        float: Exchange rate to GEL
        
    Raises:
        Exception: If API request fails or currency not found
    """
    if currency == 'GEL':
        return 1.0
    
    try:
        address = f"https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/en/json/?currencies={currency}&date={on_date}"
        response = get(address)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        if data and len(data) > 0 and 'currencies' in data[0] and len(data[0]['currencies']) > 0:
            rate = data[0]['currencies'][0]['rate']
            print(f"📈 {currency} rate on {on_date}: {rate}")
            return float(rate)
        else:
            raise ValueError(f"No rate data found for {currency} on {on_date}")
            
    except Exception as e:
        print(f"❌ Error getting rate for {currency} on {on_date}: {e}")
        raise

def load_and_process_tax_data(file_path: str, sheet_name: str = 'Data', prev_month_amount: float = 0.0) -> pd.DataFrame:
    """
    Load tax data from Excel file and process it with currency conversion.
    
    Args:
        file_path (str): Path to the Excel file containing tax data
        sheet_name (str): Name of the sheet to read from
        prev_month_amount (float): Previous month's amount in GEL (optional)
        
    Returns:
        pd.DataFrame: Processed DataFrame with currency rates and GEL amounts
    """
    print(f"📊 Loading tax data from: {file_path}")
    
    # Load the data
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    print(f"✅ Loaded {len(df)} transactions")
    
    # Convert transaction dates to proper date format if needed
    if 'Transaction date' in df.columns:
        df['Transaction date'] = pd.to_datetime(df['Transaction date']).dt.date
    
    # Get currency rates for each transaction
    print("🔄 Fetching currency rates...")
    df['rate'] = df.apply(lambda row: get_currency_rate(row['Currency'], row['Transaction date']), axis=1)
    
    # Calculate amounts in GEL
    df['amount_in_gel'] = df['Transaction amount'] * df['rate']
    
    # Calculate year-to-date total
    current_month_total = df['amount_in_gel'].sum()
    df.attrs['ytd_total'] = current_month_total + prev_month_amount
    df.attrs['current_month_total'] = current_month_total
    df.attrs['prev_month_total'] = prev_month_amount
    
    print(f"💰 Current month total: {current_month_total:,.2f} GEL")
    print(f"💰 Year-to-date total: {df.attrs['ytd_total']:,.2f} GEL")
    
    return df

def summarize_income(df: pd.DataFrame, prev_amount: float) -> dict:
    '''Field 15: year-to-date GEL; 18: Cash; 19: POS terminal; 20: Bank transaction; 21: Payment system.'''
    field15 = df['amount_in_gel'].sum() + prev_amount
    field18 = df[df['Income source'] == 'Cash']['amount_in_gel'].sum()
    field19 = df[df['Income source'] == 'POS terminal payment']['amount_in_gel'].sum()
    field20 = df[df['Income source'] == 'Bank transaction']['amount_in_gel'].sum()
    field21 = df[df['Income source'] == 'Payment system: PayPal, Wise, Deel, etc.']['amount_in_gel'].sum()
    return {
        'Field 15': field15,
        'Field 18': field18,
        'Field 19': field19,
        'Field 20': field20,
        'Field 21': field21,
    }

# ---------- Handlers ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"User {update.effective_user.id} initiated /start")
    # Show button to receive the template
    keyboard = [["Receive template"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome! Click the button below to get the tax data template:",
        reply_markup=reply_markup
    )
    return AWAIT_SELECTION

async def receive_template(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"Sending template to user {update.effective_user.id}")
    # Send the template file and instructions
    template = build_template_bytes()
    await update.message.reply_document(
        document=InputFile(template, filename="template.xlsx"),
        caption=build_instructions()
    )
    await update.message.reply_text(
        "Send your filled .xlsx file.",
        reply_markup=ReplyKeyboardRemove()
    )
    return AWAIT_FILE

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    doc = update.message.document
    logger.info(f"Received document {doc.file_name} from user {update.effective_user.id}")
    if not doc or not doc.file_name.lower().endswith(".xlsx"):
        await update.message.reply_text("Send a .xlsx file with the exact headers.")
        return AWAIT_FILE

    file = await doc.get_file()
    b = await file.download_as_bytearray()
    try:
        bio = BytesIO(b)
        # Process the tax data without previous amount
        df = load_and_process_tax_data(bio, prev_month_amount=0.0)
    except Exception as e:
        await update.message.reply_text(f"File error: {e}")
        return AWAIT_FILE
    # Store DataFrame and ask for previous month amount
    context.user_data['tax_df'] = df
    await update.message.reply_text("Received file. Please send previous period amount in GEL (e.g., 100000.00)")
    return AWAIT_PREV_AMOUNT

async def handle_prev_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    logger.info(f"User {update.effective_user.id} provided previous amount: {text}")
    try:
        prev_amount = float(text)
    except ValueError:
        await update.message.reply_text("Please send a numeric amount, e.g., 100000.00")
        return AWAIT_PREV_AMOUNT
    df = context.user_data.get('tax_df')
    if df is None:
        await update.message.reply_text("No tax file found. Send /start to begin.")
        return ConversationHandler.END
    # Summarize income
    fields = summarize_income(df, prev_amount)
    # Send summary text
    lines = [f"{k}: {v:.2f}" for k, v in fields.items()]
    await update.message.reply_text("\n".join(lines))
    # Offer to start a new tax processing
    from telegram import ReplyKeyboardMarkup
    keyboard = [["New tax"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Process another file? Click below to restart:",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"User {update.effective_user.id} canceled conversation")
    await update.message.reply_text("Canceled.")
    return ConversationHandler.END

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Set BOT_TOKEN env var.")

    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.Regex(r'^New tax$'), start)],
        states={
            AWAIT_SELECTION: [MessageHandler(filters.Regex(r'^Receive template$'), receive_template)],
            AWAIT_FILE: [MessageHandler(
                filters.Document.MimeType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                | filters.Document.FileExtension("xlsx"),
                handle_file
            )],
            AWAIT_PREV_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prev_amount)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
