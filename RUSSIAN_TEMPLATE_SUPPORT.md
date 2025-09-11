# Russian Template Support Implementation

## Overview

Added support for Russian column names in Excel templates while maintaining backward compatibility with English templates and processing pipeline.

## Features Implemented

### 1. Language-Specific Templates

- **English Template**: `Transaction amount`, `Currency`, `Transaction date`, `Income source`
- **Russian Template**: `Сумма транзакции`, `Валюта`, `Дата транзакции`, `Источник дохода`
- **File Names**: `template.xlsx` (English), `налоговый_шаблон.xlsx` (Russian)

### 2. Column Name Normalization

```python
def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Russian column names to English for processing."""
    column_mapping = {
        'Сумма транзакции': 'Transaction amount',
        'Валюта': 'Currency', 
        'Дата транзакции': 'Transaction date',
        'Источник дохода': 'Income source'
    }
```

### 3. Updated Processing Pipeline

- **File Reading**: Automatically normalizes Russian columns to English
- **Google Sheets**: Handles both Russian and English column names
- **Data Validation**: Works with normalized column names
- **Backward Compatibility**: English templates continue to work unchanged

### 4. Enhanced Template Generation

```python
def build_template_bytes(lang: str = "en") -> BytesIO:
    # Generates appropriate template based on language
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
```

## User Experience

### Russian Users Get

- ✅ **Russian column headers** in Excel template
- ✅ **Localized filename** (`налоговый_шаблон.xlsx`)
- ✅ **Same income source values** (still in English for consistency)
- ✅ **Automatic processing** of Russian column names
- ✅ **Complete sample data** showing all 4 income source types
- ✅ **Realistic sample dates** using year 1999 (clearly distinguishable from real data)

### English Users Get

- ✅ **English column headers** in Excel template
- ✅ **Standard filename** (`template.xlsx`)
- ✅ **Unchanged experience** (full backward compatibility)
- ✅ **Complete sample data** showing all 4 income source types
- ✅ **Realistic sample dates** using year 1999 (clearly distinguishable from real data)

## Technical Implementation

### Column Mapping

| Russian | English |
|---------|---------|
| Сумма транзакции | Transaction amount |
| Валюта | Currency |
| Дата транзакции | Transaction date |
| Источник дохода | Income source |

### Processing Flow

1. **Template Generation**: Language-specific column headers
2. **File Upload**: Russian columns normalized to English
3. **Data Processing**: Standard pipeline works with normalized columns
4. **Results**: Same calculation logic regardless of input language

### Income Source Values

- **Maintained in English** for consistency with validation logic
- **Users copy-paste** from detailed instructions regardless of template language
- **Prevents translation errors** in income source categorization

## Benefits

✅ **Better UX for Russian users** - Native language column headers  
✅ **Simplified data entry** - Intuitive Russian column names  
✅ **Maintained consistency** - Income sources stay standardized  
✅ **Backward compatibility** - Existing English templates still work  
✅ **Single processing pipeline** - No duplicate logic needed  
✅ **Easy maintenance** - Centralized column mapping  

## Testing Results

- ✅ English template generates correctly with 4 sample transactions
- ✅ Russian template generates correctly with 4 sample transactions
- ✅ Column normalization works properly
- ✅ Both file types process without errors
- ✅ Income source validation remains consistent
- ✅ All sample data uses year 1999 for clear distinction
- ✅ POS terminal payment example included in both templates
