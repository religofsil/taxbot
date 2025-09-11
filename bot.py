# ---------- Imports ----------
import asyncio
import os
import re
from io import BytesIO
from datetime import datetime, date

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe
from telegram import Update, InputFile, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)
from requests import get
from dotenv import load_dotenv

# ---------- Configuration ----------
load_dotenv()

import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create data collection directory if it doesn't exist
os.makedirs('data_logs', exist_ok=True)

# ---------- Data Collection Functions ----------
def log_user_start(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Log when a user starts the bot."""
    try:
        timestamp = datetime.now().isoformat()
        with open('data_logs/user_starts.txt', 'a', encoding='utf-8') as f:
            f.write(f"{timestamp},{user_id},{username or 'N/A'},{first_name or 'N/A'},{last_name or 'N/A'}\n")
    except Exception as e:
        logger.error(f"Failed to log user start: {e}")

def log_error(error_type: str, error_message: str, user_id: int = None, context: str = None):
    """Log errors with context."""
    try:
        timestamp = datetime.now().isoformat()
        with open('data_logs/errors.txt', 'a', encoding='utf-8') as f:
            f.write(f"{timestamp},{error_type},{error_message},{user_id or 'N/A'},{context or 'N/A'}\n")
    except Exception as e:
        logger.error(f"Failed to log error: {e}")

def log_user_action(user_id: int, action: str, details: str = None):
    """Log user actions for analytics."""
    try:
        timestamp = datetime.now().isoformat()
        with open('data_logs/user_actions.txt', 'a', encoding='utf-8') as f:
            f.write(f"{timestamp},{user_id},{action},{details or 'N/A'}\n")
    except Exception as e:
        logger.error(f"Failed to log user action: {e}")

# ---------- Constants ----------
AWAIT_LANGUAGE = 0
AWAIT_SELECTION = 1
AWAIT_FILE = 2
AWAIT_PREV_AMOUNT = 3

ALLOWED_CURRENCIES = {"GEL", "EUR", "USD"}
ALLOWED_SOURCES = {
    "Bank transaction",
    "POS terminal payment", 
    "Cash",
    "Payment system: PayPal, Wise, Deel, etc.",
}

# ---------- Utility Functions ----------
def to_num(s):
    """Convert string to numeric value, handling various formats."""
    if pd.isna(s): 
        return pd.NA
    s = str(s).strip()
    s = re.sub(r"[^\d,.\-]", "", s)       # drop currency/whitespace
    if s.count(",")==1 and "." not in s:  # handle 1,23 -> 1.23
        s = s.replace(",", ".")
    return pd.to_numeric(s, errors="coerce")

def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Russian column names to English for processing."""
    column_mapping = {
        'Сумма транзакции': 'Transaction amount',
        'Валюта': 'Currency',
        'Дата транзакции': 'Transaction date',
        'Источник дохода': 'Income source'
    }
    
    # Create a copy to avoid modifying original
    df_normalized = df.copy()
    
    # Rename columns using the mapping
    df_normalized.columns = [column_mapping.get(col, col) for col in df_normalized.columns]
    
    return df_normalized

def crop_to_last_transaction(df: pd.DataFrame) -> pd.DataFrame:
    """Crop DataFrame to remove empty rows after the last filled transaction."""
    # Check for both English and Russian column names
    amount_col = None
    for col in ['Transaction amount', 'Сумма транзакции']:
        if col in df.columns:
            amount_col = col
            break
    
    if amount_col is None:
        return df
    
    # Find the last row with a non-null Transaction amount
    last_filled_idx = df[amount_col].last_valid_index()
    
    if last_filled_idx is not None:
        # Crop the DataFrame to include only up to the last filled row
        df = df.iloc[:last_filled_idx + 1].copy()
    
    return df

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

def get_tax_dataframe_from_file(file_bytes: BytesIO) -> pd.DataFrame:
    """Read and validate tax data from .xlsx file bytes."""
    df = pd.read_excel(BytesIO(file_bytes), sheet_name='Data')
    
    # Normalize column names (Russian to English)
    df = normalize_column_names(df)
    df = crop_to_last_transaction(df)
    
    # Validate required columns
    required_columns = ['Transaction amount', 'Currency', 'Transaction date', 'Income source']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    return df

def get_tax_dataframe_from_sheet(link: str, creds_path: str) -> pd.DataFrame:
    """Read and validate tax data from Google Sheets."""
    sheet_id_match = re.search(r"/d/([a-zA-Z0-9_-]+)", link)
    if not sheet_id_match:
        raise ValueError("Invalid Google Sheets link")
    sheet_id = sheet_id_match.group(1)
    
    creds = Credentials.from_service_account_file(
        creds_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).sheet1
    df = get_as_dataframe(sheet, evaluate_formulas=True, header=0)
    
    # Normalize column names (Russian to English)
    df = normalize_column_names(df)
    
    # Clean up the DataFrame
    df = crop_to_last_transaction(df)
    
    # Convert Transaction amount to numeric (handle both original and normalized names)
    amount_col = 'Transaction amount'
    if amount_col in df.columns:
        df[amount_col] = df[amount_col].map(to_num)
    
    return df

def process_tax_dataframe(df: pd.DataFrame, prev_month_amount: float = 0.0) -> pd.DataFrame:
    """Process tax DataFrame with currency conversion and calculations."""
    print(f"✅ Processing {len(df)} transactions")
    
    # Convert transaction dates to proper date format
    if 'Transaction date' in df.columns:
        df['Transaction date'] = pd.to_datetime(df['Transaction date'],
            format="%d.%m.%Y",   # matches 14.08.2025
            errors="coerce"      # invalid dates become NaT
        ).dt.date
    
    # Get currency rates for each transaction
    print("🔄 Fetching currency rates...")
    df['rate'] = df.apply(lambda row: get_currency_rate(row['Currency'], row['Transaction date']), axis=1)
    
    # Calculate amounts in GEL
    df['amount_in_gel'] = df['Transaction amount'] * df['rate']
    
    # Calculate totals
    current_month_total = df['amount_in_gel'].sum()
    df.attrs['ytd_total'] = current_month_total + prev_month_amount
    df.attrs['current_month_total'] = current_month_total
    df.attrs['prev_month_total'] = prev_month_amount
    
    print(f"💰 Current month total: {current_month_total:,.2f} GEL")
    print(f"💰 Year-to-date total: {df.attrs['ytd_total']:,.2f} GEL")
    
    return df

def summarize_income(df: pd.DataFrame, prev_amount: float) -> dict:
    """Summarize income by fields for tax declaration."""
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

# ---------- Template Generation ----------
def build_template_bytes(lang: str = "en") -> BytesIO:
    """Build an Excel template file for tax data entry."""
    import xlsxwriter
    
    # Create a new workbook and worksheet
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Data')
    
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D7E4BC',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'border': 1
    })
    
    date_format = workbook.add_format({
        'num_format': 'dd.mm.yyyy',
        'border': 1
    })
    
    # Define headers based on language
    if lang == "ru":
        headers = ['Сумма транзакции', 'Валюта', 'Дата транзакции', 'Источник дохода']
        sample_data = [
            [1000, 'USD', '01.01.1999', 'Bank transaction'],
            [500, 'EUR', '02.01.1999', 'Payment system: PayPal, Wise, Deel, etc.'],
            [200, 'GEL', '03.01.1999', 'Cash'],
            [300, 'USD', '04.01.1999', 'POS terminal payment'],
        ]
    else:
        headers = ['Transaction amount', 'Currency', 'Transaction date', 'Income source']
        sample_data = [
            [1000, 'USD', '01.01.1999', 'Bank transaction'],
            [500, 'EUR', '02.01.1999', 'Payment system: PayPal, Wise, Deel, etc.'],
            [200, 'GEL', '03.01.1999', 'Cash'],
            [300, 'USD', '04.01.1999', 'POS terminal payment'],
        ]
    
    # Write headers
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Set column widths
    worksheet.set_column(0, 0, 18)  # Transaction amount
    worksheet.set_column(1, 1, 10)  # Currency
    worksheet.set_column(2, 2, 18)  # Transaction date
    worksheet.set_column(3, 3, 25)  # Income source
    
    # Add sample data
    for row, data in enumerate(sample_data, 1):
        for col, value in enumerate(data):
            if col == 2:  # Date column
                worksheet.write_datetime(row, col, datetime.strptime(value, '%d.%m.%Y'), date_format)
            else:
                worksheet.write(row, col, value, cell_format)
    
    # Add data validation for currency
    worksheet.data_validation(1, 1, 1000, 1, {
        'validate': 'list',
        'source': ['GEL', 'USD', 'EUR']
    })
    
    # Add data validation for income source
    income_sources = [
        'Bank transaction',
        'POS terminal payment',
        'Cash',
        'Payment system: PayPal, Wise, Deel, etc.'
    ]
    worksheet.data_validation(1, 3, 1000, 3, {
        'validate': 'list',
        'source': income_sources
    })
    
    workbook.close()
    output.seek(0)
    return output

def build_instructions() -> str:
    """Build instruction text for the template."""
    return (
        "📊 TAX CALCULATION BOT FOR GEORGIA\n\n"
        "This bot helps you calculate tax declaration fields for Georgia Revenue Service.\n\n"
        "📋 HOW IT WORKS:\n"
        "1. Download the Excel template below\n"
        "2. Fill in your transaction data\n"
        "3. Send the completed file back to this bot\n"
        "4. Get calculated amounts for tax declaration fields\n\n"
        "📝 BASIC RULES:\n"
        "• Columns: Transaction amount, Currency, Transaction date, Income source\n"
        "• Currency: GEL, EUR, USD\n"
        "• Date: DD.MM.YYYY (e.g., 14.08.2025)\n"
        "• Formats: Excel (.xlsx) or Google Sheets links"
    )

def build_detailed_income_instructions_en() -> str:
    """Build detailed income source instructions in English."""
    return (
        "📝 INCOME SOURCE - WRITE EXACTLY:\n\n"
        "• \"Bank transaction\" - for:\n"
        "  ✓ Wire transfers to your bank account\n"
        "  ✓ Direct deposits from clients\n"
        "  ✓ International bank transfers (SWIFT)\n"
        "  ✓ Local bank transfers within Georgia\n\n"
        "• \"POS terminal payment\" - for:\n"
        "  ✓ Card payments at physical locations\n"
        "  ✓ Contactless payments (NFC)\n"
        "  ✓ Chip & PIN transactions\n"
        "  ✓ Any payment via card reader/terminal\n\n"
        "• \"Cash\" - for:\n"
        "  ✓ Physical cash payments received\n"
        "  ✓ Cash tips or bonuses\n"
        "  ✓ Cash exchanges (currency to cash)\n\n"
        "• \"Payment system: PayPal, Wise, Deel, etc.\" - for:\n"
        "  ✓ PayPal payments\n"
        "  ✓ Wise (ex-TransferWise) transfers\n"
        "  ✓ Deel, Upwork, Fiverr payments\n"
        "  ✓ Stripe, Square payments\n"
        "  ✓ Skrill, Payoneer, Remitly\n"
        "  ✓ Any online payment platform\n\n"
        "⚠️ IMPORTANT: Copy-paste the exact text from the options above!"
    )

def build_detailed_income_instructions_ru() -> str:
    """Build detailed income source instructions in Russian."""
    return (
        "📝 ИСТОЧНИК ДОХОДА - ПИШИТЕ ТОЧНО:\n\n"
        "• \"Bank transaction\" - для:\n"
        "  ✓ Банковских переводов на ваш счет\n"
        "  ✓ Прямых депозитов от клиентов\n"
        "  ✓ Международных переводов (SWIFT)\n"
        "  ✓ Местных переводов внутри Грузии\n\n"
        "• \"POS terminal payment\" - для:\n"
        "  ✓ Оплат картой в физических точках\n"
        "  ✓ Бесконтактных платежей (NFC)\n"
        "  ✓ Транзакций чип+PIN\n"
        "  ✓ Любых платежей через терминал\n\n"
        "• \"Cash\" - для:\n"
        "  ✓ Наличных платежей\n"
        "  ✓ Чаевых или бонусов наличными\n"
        "  ✓ Обмена валюты на наличные\n\n"
        "• \"Payment system: PayPal, Wise, Deel, etc.\" - для:\n"
        "  ✓ Платежей PayPal\n"
        "  ✓ Переводов Wise (ex-TransferWise)\n"
        "  ✓ Выплат Deel, Upwork, Fiverr\n"
        "  ✓ Платежей Stripe, Square\n"
        "  ✓ Skrill, Payoneer, Remitly\n"
        "  ✓ Любых онлайн-платформ\n\n"
        "⚠️ ВАЖНО: Копируйте точный текст из вариантов выше!"
    )

# ---------- Bot Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command - show language selection."""
    user = update.effective_user
    logger.info(f"User {user.id} initiated /start")
    
    # Log user start for data collection
    log_user_start(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    log_user_action(user.id, "start_bot", "Initial /start command")
    
    keyboard = [["Русский", "English"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Выберите язык / Choose your language:",
        reply_markup=reply_markup
    )
    return AWAIT_LANGUAGE

async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle language selection."""
    user = update.effective_user
    lang = update.message.text.strip().lower()
    
    if lang in ["русский", "ru"]:
        context.user_data["lang"] = "ru"
        log_user_action(user.id, "language_selected", "Russian")
        welcome = (
            "🎉 Добро пожаловать в бот для расчета налогов в Грузии!\n\n"
            "Этот бот поможет вам автоматически рассчитать поля 15, 18-21 налоговой декларации "
            "на основе ваших транзакций с конвертацией валют по курсу Национального банка Грузии.\n\n"
            "Нажмите кнопку ниже, чтобы получить шаблон для ввода данных:"
        )
        button = "Получить шаблон"
    else:
        context.user_data["lang"] = "en"
        log_user_action(user.id, "language_selected", "English")
        welcome = (
            "🎉 Welcome to the Georgia Tax Calculation Bot!\n\n"
            "This bot will help you automatically calculate fields 15, 18-21 of your tax declaration "
            "based on your transactions with currency conversion using National Bank of Georgia rates.\n\n"
            "Click the button below to get the data entry template:"
        )
        button = "Receive template"
    
    keyboard = [[button]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(welcome, reply_markup=reply_markup)
    return AWAIT_SELECTION

async def receive_template(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send template file and instructions."""
    user = update.effective_user
    logger.info(f"Sending template to user {user.id}")
    lang = context.user_data.get("lang", "en")
    
    # Log template download
    log_user_action(user.id, "template_requested", f"Language: {lang}")
    
    template = build_template_bytes(lang)
    
    if lang == "ru":
        caption = (
            "📊 БОТ ДЛЯ РАСЧЕТА НАЛОГОВ В ГРУЗИИ\n\n"
            "Этот бот поможет вам рассчитать поля налоговой декларации для Дома Юстиции Грузии.\n\n"
            "📋 КАК ЭТО РАБОТАЕТ:\n"
            "1. Скачайте Excel шаблон ниже\n"
            "2. Заполните данные о ваших транзакциях\n"
            "3. Отправьте заполненный файл обратно боту\n"
            "4. Получите рассчитанные суммы для полей декларации\n\n"
            "📝 ОСНОВНЫЕ ПРАВИЛА:\n"
            "• Столбцы: Сумма транзакции, Валюта, Дата транзакции, Источник дохода\n"
            "• Валюта: GEL, EUR, USD\n"
            "• Дата: ДД.ММ.ГГГГ (например, 14.08.2025)\n"
            "• Форматы: Excel (.xlsx) или ссылки Google Sheets"
        )
        reply = "Отправьте заполненный .xlsx файл или ссылку на Google Sheets."
        sheets_link = "Вы также можете сделать копию шаблона в Google Sheets: https://docs.google.com/spreadsheets/d/1no-hnrWP8mWEREK97oVAUJ4-Ki2GP9wkbgNPEKtfJMo/edit?usp=sharing"
        detailed_instructions = build_detailed_income_instructions_ru()
        filename = "налоговый_шаблон.xlsx"
    else:
        caption = build_instructions()
        reply = "Send your filled .xlsx file or Google Sheets link."
        sheets_link = "You can also make a copy of the template in Google Sheets: https://docs.google.com/spreadsheets/d/1no-hnrWP8mWEREK97oVAUJ4-Ki2GP9wkbgNPEKtfJMo/edit?usp=sharing"
        detailed_instructions = build_detailed_income_instructions_en()
        filename = "template.xlsx"
    
    await update.message.reply_document(
        document=InputFile(template, filename=filename),
        caption=caption
    )
    await update.message.reply_text(detailed_instructions)
    await update.message.reply_text(reply, reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text(sheets_link)
    return AWAIT_FILE

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle file upload or Google Sheets link."""
    user = update.effective_user
    lang = context.user_data.get("lang", "en")
    
    # Handle document upload
    if update.message.document:
        doc = update.message.document
        logger.info(f"Received document {doc.file_name} from user {user.id}")
        log_user_action(user.id, "file_uploaded", f"Filename: {doc.file_name}, Size: {doc.file_size}")
        
        if not doc.file_name.lower().endswith(".xlsx"):
            log_error("InvalidFileType", f"User uploaded non-xlsx file: {doc.file_name}", user.id, "file_upload")
            msg = "Send a .xlsx file with the exact headers." if lang == "en" else "Отправьте .xlsx файл с правильными заголовками."
            await update.message.reply_text(msg)
            return AWAIT_FILE
        
        file = await doc.get_file()
        b = await file.download_as_bytearray()
        
        try:
            df = get_tax_dataframe_from_file(b)
            df = process_tax_dataframe(df, prev_month_amount=0.0)
            log_user_action(user.id, "file_processed_success", f"Rows: {len(df)}")
        except Exception as e:
            log_error("FileProcessingError", str(e), user.id, f"file_upload:{doc.file_name}")
            msg = f"File error: {e}" if lang == "en" else f"Ошибка файла: {e}"
            await update.message.reply_text(msg)
            return AWAIT_FILE
    
    # Handle Google Sheets link
    elif update.message.text and "docs.google.com/spreadsheets" in update.message.text:
        link = update.message.text.strip()
        logger.info(f"Received Google Sheets link: {link}")
        log_user_action(user.id, "google_sheet_submitted", f"Link: {link}")
        
        try:
            creds_path = os.getenv('GOOGLE_KEY_PATH', 'service_account.json')
            df = get_tax_dataframe_from_sheet(link, creds_path)
            df = process_tax_dataframe(df, prev_month_amount=0.0)
            log_user_action(user.id, "google_sheet_processed_success", f"Rows: {len(df)}")
        except Exception as e:
            log_error("GoogleSheetError", str(e), user.id, f"google_sheet:{link}")
            msg = f"Error reading Google Sheet: {e}" if lang == "en" else f"Ошибка чтения Google Sheets: {e}"
            await update.message.reply_text(msg)
            return AWAIT_FILE
    
    else:
        log_user_action(user.id, "invalid_input", "Neither xlsx file nor Google Sheets link")
        msg = "Send a .xlsx file or a Google Sheets link." if lang == "en" else "Отправьте .xlsx файл или ссылку на Google Sheets."
        await update.message.reply_text(msg)
        return AWAIT_FILE
    
    # Store DataFrame and ask for previous amount
    context.user_data['tax_df'] = df
    msg = ("Received file. Please send previous period amount (field 15 from previous month declaration) in GEL (e.g., 100000.00)" 
           if lang == "en" else 
           "Файл получен. Пожалуйста, отправьте сумму за предыдущий период (поле 15 из декларации за предыдущий месяц) в GEL (например, 100000.00)")
    await update.message.reply_text(msg)
    return AWAIT_PREV_AMOUNT

async def handle_prev_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle previous amount input and calculate final results."""
    user = update.effective_user
    text = update.message.text.strip()
    logger.info(f"User {user.id} provided previous amount: {text}")
    lang = context.user_data.get("lang", "en")
    
    try:
        prev_amount = float(text)
        log_user_action(user.id, "prev_amount_provided", f"Amount: {prev_amount}")
    except ValueError:
        log_error("InvalidAmount", f"User provided non-numeric amount: {text}", user.id, "prev_amount_input")
        msg = ("Please send a numeric amount, e.g., 100000.00" 
               if lang == "en" else 
               "Пожалуйста, отправьте числовое значение, например, 100000.00")
        await update.message.reply_text(msg)
        return AWAIT_PREV_AMOUNT
    
    df = context.user_data.get('tax_df')
    if df is None:
        log_error("MissingDataFrame", "No tax DataFrame found in user context", user.id, "calculation")
        msg = ("No tax file found. Send /start to begin." 
               if lang == "en" else 
               "Файл не найден. Отправьте /start для начала.")
        await update.message.reply_text(msg)
        return ConversationHandler.END
    
    # Calculate fields
    fields = summarize_income(df, prev_amount)
    
    # Log successful calculation
    log_user_action(user.id, "calculation_completed", f"Field15: {fields['Field 15']:.2f}, Transactions: {len(df)}")
    
    if lang == "ru":
        field_names = {
            'Field 15': 'Поле 15 (лари с начала года)',
            'Field 18': 'Поле 18 (Наличные)',
            'Field 19': 'Поле 19 (POS-терминал)',
            'Field 20': 'Поле 20 (Банковский перевод)',
            'Field 21': 'Поле 21 (Платежная система)',
        }
        lines = [f"{field_names.get(k, k)}: {v:.2f}" for k, v in fields.items()]
        restart = "Новый расчет"
        msg = "Обработать другой файл? Нажмите ниже, чтобы начать заново:"
        catebi = "Если бот был полезен, поддержите Catebi — благотворительную организацию, которая стерилизует бездомных кошек в Грузии: https://catebi.ge/donate"
    else:
        lines = [f"{k}: {v:.2f}" for k, v in fields.items()]
        restart = "New tax"
        msg = "Process another file? Click below to restart:"
        catebi = "If you found this bot useful, please consider donating to Catebi — a non-profit Trap-Neuter-Return organization for stray cats in Georgia: https://catebi.ge/donate"
    
    # Send results
    await update.message.reply_text("\n".join(lines))
    await update.message.reply_text(catebi)
    
    # Offer restart option
    keyboard = [[restart]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(msg, reply_markup=reply_markup)
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle conversation cancellation."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "N/A"
    first_name = update.effective_user.first_name or "N/A"
    
    logger.info(f"User {user_id} canceled conversation")
    log_user_action(user_id, username, first_name, "conversation_canceled", "User manually canceled the conversation")
    
    await update.message.reply_text("Canceled.")
    return ConversationHandler.END

# ---------- Error Handler ----------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler to log unexpected errors."""
    try:
        user_id = None
        username = "N/A"
        first_name = "N/A"
        
        if update and hasattr(update, 'effective_user') and update.effective_user:
            user_id = update.effective_user.id
            username = update.effective_user.username or "N/A"
            first_name = update.effective_user.first_name or "N/A"
        
        error_message = f"Unexpected error: {str(context.error)}"
        logger.error(error_message, exc_info=context.error)
        
        if user_id:
            log_error(user_id, username, first_name, "unexpected_error", error_message)
        else:
            log_error("unknown", "N/A", "N/A", "unexpected_error", error_message)
            
    except Exception as e:
        logger.error(f"Error in error handler: {str(e)}")

# ---------- Main Application ----------
def main():
    """Main application entry point."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Set BOT_TOKEN env var.")

    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start), 
            MessageHandler(filters.Regex(r'^New tax$|^Новый расчет$'), start)
        ],
        states={
            AWAIT_LANGUAGE: [
                MessageHandler(filters.Regex(r'^Русский$|^English$'), select_language)
            ],
            AWAIT_SELECTION: [
                MessageHandler(filters.Regex(r'^Receive template$|^Получить шаблон$'), receive_template)
            ],
            AWAIT_FILE: [
                MessageHandler(
                    filters.Document.MimeType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    | filters.Document.FileExtension("xlsx"),
                    handle_file
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_file
                )
            ],
            AWAIT_PREV_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prev_amount)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
