# Data Collection Implementation

## Overview

This document describes the comprehensive data collection system implemented in the Georgian Tax Calculator Telegram Bot. The system tracks user interactions, calculates usage statistics, and logs errors for monitoring and improvement purposes.

## Data Collection Functions

### 1. `log_user_start(user_id, username, first_name)`

Records when a user starts a new conversation with the bot.

**File:** `user_data.log`
**Format:** `timestamp | USER_START | user_id | username | first_name`

### 2. `log_user_action(user_id, username, first_name, action, details)`

Records specific user actions throughout the conversation flow.

**File:** `user_data.log`
**Format:** `timestamp | ACTION_TYPE | user_id | username | first_name | details`

**Tracked Actions:**

- `LANGUAGE_SELECTED` - User selects Russian or English
- `TEMPLATE_REQUESTED` - User requests a template download
- `FILE_UPLOAD_STARTED` - User begins file upload process
- `XLSX_FILE_PROCESSED` - Excel file successfully processed
- `GOOGLE_SHEETS_PROCESSED` - Google Sheets link successfully processed
- `PREV_AMOUNT_ENTERED` - User enters previous tax amount
- `CALCULATION_COMPLETED` - Tax calculation successfully completed
- `CONVERSATION_CANCELED` - User cancels the conversation

### 3. `log_error(user_id, username, first_name, error_type, error_message)`

Records errors and exceptions that occur during bot operation.

**File:** `errors.log`
**Format:** `timestamp | user_id | username | first_name | error_type | error_message`

**Tracked Error Types:**

- `file_processing_error` - Issues with file upload/processing
- `google_sheets_error` - Problems accessing Google Sheets
- `api_error` - External API failures (e.g., NBG currency API)
- `calculation_error` - Tax calculation failures
- `unexpected_error` - Unexpected system errors (via global error handler)

## Integration Points

### Handler Functions

All bot handler functions include appropriate logging calls:

1. **`start()`** - Logs user start events
2. **`select_language()`** - Logs language selection
3. **`receive_template()`** - Logs template requests
4. **`handle_file()`** - Logs file processing (success/error)
5. **`handle_prev_amount()`** - Logs calculation completion
6. **`cancel()`** - Logs conversation cancellation

### Global Error Handler

The `error_handler()` function catches any unexpected errors and logs them with full context.

## Log File Structure

### user_data.log

```text
2025-09-11 09:49:01 | USER_START | 12345 | testuser | Test User
2025-09-11 09:49:02 | LANGUAGE_SELECTED | 12345 | testuser | Test User | Selected English
2025-09-11 09:49:03 | TEMPLATE_REQUESTED | 12345 | testuser | Test User | English template
2025-09-11 09:49:04 | FILE_UPLOAD_STARTED | 12345 | testuser | Test User | Expecting XLSX file
2025-09-11 09:49:05 | XLSX_FILE_PROCESSED | 12345 | testuser | Test User | 15 transactions processed
2025-09-11 09:49:06 | PREV_AMOUNT_ENTERED | 12345 | testuser | Test User | Amount: 150.0 GEL
2025-09-11 09:49:07 | CALCULATION_COMPLETED | 12345 | testuser | Test User | New tax: 45.2 GEL, Total: 195.2 GEL
```

### errors.log

```text
2025-09-11 09:49:01 | 12345 | testuser | Test User | file_processing_error | Invalid XLSX format
2025-09-11 09:49:02 | 12345 | testuser | Test User | google_sheets_error | Unable to access spreadsheet
2025-09-11 09:49:03 | 12345 | testuser | Test User | api_error | NBG API timeout
```

## Configuration

### Log File Locations

- `user_data.log` - User interaction logs
- `errors.log` - Error and exception logs

### Data Retention

- Log files append new entries without automatic rotation
- Manual cleanup may be needed for production environments
- Consider implementing log rotation for high-volume usage

## Privacy Considerations

### Collected Data

- User ID (Telegram user identifier)
- Username (if set by user)
- First name (if set by user)
- Interaction timestamps
- Error messages (may contain file names or other details)

### Data Usage

- Monitor bot performance and usage patterns
- Identify and fix common errors
- Improve user experience based on interaction data
- Generate usage statistics

### Security

- Log files contain user identifiers but no sensitive financial data
- Error logs may contain file names or system paths
- Ensure proper file permissions on log files
- Consider encryption for production environments

## Analytics Opportunities

### User Metrics

- Total unique users
- Language preferences
- Usage patterns by time/date
- Conversion rates (start → completion)

### System Metrics

- Error rates by function
- Most common error types
- Processing success rates
- Performance bottlenecks

### Business Insights

- Feature usage patterns
- User drop-off points
- Peak usage times
- Geographic distribution (if available)

## Maintenance

### Regular Tasks

1. Monitor log file sizes
2. Review error patterns
3. Archive old logs if needed
4. Update tracking for new features

### Troubleshooting

1. Check log files for recent errors
2. Verify write permissions on log files
3. Ensure adequate disk space
4. Monitor for log rotation needs

## Future Enhancements

### Potential Additions

- Database storage for structured queries
- Real-time dashboards
- Automated alerting for error spikes
- User session tracking
- A/B testing support
- Export functionality for analytics tools

### Integration Options

- Google Analytics
- Grafana/Prometheus monitoring
- Database logging (PostgreSQL, MongoDB)
- Cloud logging services (AWS CloudWatch, Google Cloud Logging)
