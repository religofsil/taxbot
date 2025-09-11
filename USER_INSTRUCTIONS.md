# Tax Bot User Instructions Summary

## What Users See When They Start the Bot

### 1. Language Selection

When users send `/start`, they see:

```text
Выберите язык / Choose your language:
[Русский] [English]
```

### 2. Welcome Message (English)

```text
🎉 Welcome to the Georgia Tax Calculation Bot!

This bot will help you automatically calculate fields 15, 18-21 of your tax declaration based on your transactions with currency conversion using National Bank of Georgia rates.

Click the button below to get the data entry template:
[Receive template]
```

### 2. Welcome Message (Russian)

```text
🎉 Добро пожаловать в бот для расчета налогов в Грузии!

Этот бот поможет вам автоматически рассчитать поля 15, 18-21 налоговой декларации на основе ваших транзакций с конвертацией валют по курсу Национального банка Грузии.

Нажмите кнопку ниже, чтобы получить шаблон для ввода данных:
[Получить шаблон]
```

### 3. Detailed Instructions with Template (English)

When users click "Receive template", they get:

**Excel file attachment** with caption:

```text
📊 TAX CALCULATION BOT FOR GEORGIA

This bot helps you calculate tax declaration fields for Georgia Revenue Service.

📋 HOW IT WORKS:
1. Download the Excel template below
2. Fill in your transaction data
3. Send the completed file back to this bot
4. Get calculated amounts for tax declaration fields

📝 TEMPLATE RULES:
• Columns (exact order): Transaction amount, Currency, Transaction date, Income source
• Currency: Only GEL, EUR, USD are supported
• Date format: DD.MM.YYYY (e.g., 14.08.2025)

📝 INCOME SOURCE - WRITE EXACTLY:
• "Bank transaction" - for:
  ✓ Wire transfers to your bank account
  ✓ Direct deposits from clients
  ✓ International bank transfers (SWIFT)
  ✓ Local bank transfers within Georgia

• "POS terminal payment" - for:
  ✓ Card payments at physical locations
  ✓ Contactless payments (NFC)
  ✓ Chip & PIN transactions
  ✓ Any payment via card reader/terminal

• "Cash" - for:
  ✓ Physical cash payments received
  ✓ Cash tips or bonuses
  ✓ Cash exchanges (currency to cash)

• "Payment system: PayPal, Wise, Deel, etc." - for:
  ✓ PayPal payments
  ✓ Wise (ex-TransferWise) transfers
  ✓ Deel, Upwork, Fiverr payments
  ✓ Stripe, Square payments
  ✓ Skrill, Payoneer, Remitly
  ✓ Any online payment platform

💡 SUPPORTED FORMATS:
• Excel (.xlsx) files
• Google Sheets links

🔄 The bot will:
• Convert all amounts to GEL using National Bank rates
• Calculate totals for declaration fields 15, 18-21
• Show breakdown by income source

⚠️ Make sure to follow the exact column order and data formats!
```

**Follow-up messages:**

```text
Send your filled .xlsx file or Google Sheets link.

You can also make a copy of the template in Google Sheets: 
https://docs.google.com/spreadsheets/d/1no-hnrWP8mWEREK97oVAUJ4-Ki2GP9wkbgNPEKtfJMo/edit?usp=sharing
```

### 3. Detailed Instructions with Template (Russian)

When users click "Получить шаблон", they get:

**Excel file attachment** with caption:

```text
📊 БОТ ДЛЯ РАСЧЕТА НАЛОГОВ В ГРУЗИИ

Этот бот поможет вам рассчитать поля налоговой декларации для Дома Юстиции Грузии.

📋 КАК ЭТО РАБОТАЕТ:
1. Скачайте Excel шаблон ниже
2. Заполните данные о ваших транзакциях
3. Отправьте заполненный файл обратно боту
4. Получите рассчитанные суммы для полей декларации

📝 ПРАВИЛА ШАБЛОНА:
• Столбцы (точный порядок): Сумма транзакции, Валюта, Дата транзакции, Источник дохода
• Валюта: Поддерживаются только GEL, EUR, USD
• Формат даты: ДД.ММ.ГГГГ (например, 14.08.2025)

📝 ИСТОЧНИК ДОХОДА - ПИШИТЕ ТОЧНО:
• "Bank transaction" - для:
  ✓ Банковских переводов на ваш счет
  ✓ Прямых депозитов от клиентов
  ✓ Международных переводов (SWIFT)
  ✓ Местных переводов внутри Грузии

• "POS terminal payment" - для:
  ✓ Оплат картой в физических точках
  ✓ Бесконтактных платежей (NFC)
  ✓ Транзакций чип+PIN
  ✓ Любых платежей через терминал

• "Cash" - для:
  ✓ Наличных платежей
  ✓ Чаевых или бонусов наличными
  ✓ Обмена валюты на наличные

• "Payment system: PayPal, Wise, Deel, etc." - для:
  ✓ Платежей PayPal
  ✓ Переводов Wise (ex-TransferWise)
  ✓ Выплат Deel, Upwork, Fiverr
  ✓ Платежей Stripe, Square
  ✓ Skrill, Payoneer, Remitly
  ✓ Любых онлайн-платформ

⚠️ IMPORTANT: Copy-paste the exact text from the options above!

💡 ПОДДЕРЖИВАЕМЫЕ ФОРМАТЫ:
• Excel файлы (.xlsx)
• Ссылки на Google Sheets

🔄 БОТ ВЫПОЛНИТ:
• Конвертацию всех сумм в лари по курсу Нацбанка
• Расчет итогов для полей декларации 15, 18-21
• Разбивку по источникам дохода

⚠️ ВАЖНО: Копируйте точный текст из вариантов выше!
```

**Follow-up messages:**

```text
Отправьте заполненный .xlsx файл или ссылку на Google Sheets.

Вы также можете сделать копию шаблона в Google Sheets: 
https://docs.google.com/spreadsheets/d/1no-hnrWP8mWEREK97oVAUJ4-Ki2GP9wkbgNPEKtfJMo/edit?usp=sharing
```

## Key Features Highlighted in Instructions

✅ **Clear Purpose**: Tax calculation for Georgia Revenue Service  
✅ **Step-by-step Process**: 4 simple steps explained  
✅ **Exact Requirements**: Column order, date format, currency options  
✅ **Multiple Input Options**: Excel files and Google Sheets  
✅ **Automatic Features**: Currency conversion, field calculations  
✅ **Visual Elements**: Emojis for better readability  
✅ **Bilingual Support**: Full Russian and English versions  
✅ **Russian Templates**: Native Russian column headers for Russian users  
✅ **External Template**: Google Sheets link provided  

The instructions are comprehensive, user-friendly, and provide all necessary information for users to successfully use the bot. Russian users receive templates with Russian column headers while maintaining the same processing pipeline.
