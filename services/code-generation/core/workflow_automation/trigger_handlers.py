"""
Trigger handlers for workflow automation
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import croniter

logger = logging.getLogger(__name__)


def handle_manual_trigger(trigger_config: Dict[str, Any], event_data: Dict[str, Any] = None) -> bool:
    """
    Handle manual workflow triggers
    
    Args:
        trigger_config: Trigger configuration
        event_data: Event data (not used for manual triggers)
        
    Returns:
        True if trigger should fire
    """
    # Manual triggers always fire when explicitly invoked
    return True


def handle_scheduled_trigger(trigger_config: Dict[str, Any], event_data: Dict[str, Any] = None) -> bool:
    """
    Handle scheduled workflow triggers using cron expressions
    
    Args:
        trigger_config: Trigger configuration with cron schedule
        event_data: Current time data
        
    Returns:
        True if trigger should fire based on schedule
    """
    cron_expression = trigger_config.get("cron_expression")
    if not cron_expression:
        logger.error("No cron expression provided for scheduled trigger")
        return False
    
    try:
        # Get current time or use provided time
        current_time = datetime.now()
        if event_data and "current_time" in event_data:
            current_time = datetime.fromisoformat(event_data["current_time"])
        
        # Check if current time matches cron schedule
        cron = croniter.croniter(cron_expression, current_time)
        
        # Check if we're within the trigger window (e.g., last minute)
        last_trigger_time = cron.get_prev(datetime)
        time_diff = (current_time - last_trigger_time).total_seconds()
        
        # Trigger if within the last minute
        return time_diff < 60
        
    except Exception as e:
        logger.error(f"Error evaluating cron expression '{cron_expression}': {e}")
        return False


def handle_schema_change_trigger(trigger_config: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
    """
    Handle schema change triggers
    
    Args:
        trigger_config: Trigger configuration with change filters
        event_data: Schema change event data
        
    Returns:
        True if trigger should fire based on schema changes
    """
    if not event_data or "change_type" not in event_data:
        return False
    
    change_type = event_data.get("change_type")
    table_name = event_data.get("table_name", "")
    database_name = event_data.get("database_name", "")
    
    # Check change type filters
    allowed_change_types = trigger_config.get("change_types", [])
    if allowed_change_types and change_type not in allowed_change_types:
        return False
    
    # Check table name patterns
    table_patterns = trigger_config.get("table_patterns", [])
    if table_patterns:
        if not any(re.match(pattern, table_name) for pattern in table_patterns):
            return False
    
    # Check excluded tables
    excluded_tables = trigger_config.get("excluded_tables", [])
    if table_name in excluded_tables:
        return False
    
    # Check database filters
    allowed_databases = trigger_config.get("databases", [])
    if allowed_databases and database_name not in allowed_databases:
        return False
    
    # Check severity filters
    severity = event_data.get("severity", "low")
    min_severity = trigger_config.get("min_severity", "low")
    
    severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    if severity_levels.get(severity, 0) < severity_levels.get(min_severity, 0):
        return False
    
    logger.info(f"Schema change trigger fired for {change_type} on {table_name}")
    return True


def handle_file_upload_trigger(trigger_config: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
    """
    Handle file upload triggers
    
    Args:
        trigger_config: Trigger configuration with file filters
        event_data: File upload event data
        
    Returns:
        True if trigger should fire based on file upload
    """
    if not event_data or "file_path" not in event_data:
        return False
    
    file_path = event_data.get("file_path", "")
    file_name = event_data.get("file_name", "")
    file_size = event_data.get("file_size", 0)
    upload_user = event_data.get("upload_user", "")
    
    # Check file extension filters
    allowed_extensions = trigger_config.get("allowed_extensions", [])
    if allowed_extensions:
        file_extension = file_path.split('.')[-1].lower()
        if file_extension not in [ext.lower() for ext in allowed_extensions]:
            return False
    
    # Check file name patterns
    file_patterns = trigger_config.get("file_patterns", [])
    if file_patterns:
        if not any(re.match(pattern, file_name) for pattern in file_patterns):
            return False
    
    # Check file size limits
    max_file_size = trigger_config.get("max_file_size")
    if max_file_size and file_size > max_file_size:
        return False
    
    min_file_size = trigger_config.get("min_file_size")
    if min_file_size and file_size < min_file_size:
        return False
    
    # Check upload path filters
    allowed_paths = trigger_config.get("allowed_paths", [])
    if allowed_paths:
        if not any(file_path.startswith(path) for path in allowed_paths):
            return False
    
    # Check user filters
    allowed_users = trigger_config.get("allowed_users", [])
    if allowed_users and upload_user not in allowed_users:
        return False
    
    logger.info(f"File upload trigger fired for {file_name}")
    return True


def handle_api_request_trigger(trigger_config: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
    """
    Handle API request triggers
    
    Args:
        trigger_config: Trigger configuration with API filters
        event_data: API request event data
        
    Returns:
        True if trigger should fire based on API request
    """
    if not event_data:
        return False
    
    endpoint = event_data.get("endpoint", "")
    method = event_data.get("method", "")
    user_id = event_data.get("user_id", "")
    request_data = event_data.get("request_data", {})
    
    # Check endpoint patterns
    endpoint_patterns = trigger_config.get("endpoint_patterns", [])
    if endpoint_patterns:
        if not any(re.match(pattern, endpoint) for pattern in endpoint_patterns):
            return False
    
    # Check HTTP methods
    allowed_methods = trigger_config.get("allowed_methods", [])
    if allowed_methods and method.upper() not in [m.upper() for m in allowed_methods]:
        return False
    
    # Check user filters
    allowed_users = trigger_config.get("allowed_users", [])
    if allowed_users and user_id not in allowed_users:
        return False
    
    # Check request data filters
    data_filters = trigger_config.get("data_filters", {})
    for filter_key, filter_value in data_filters.items():
        if filter_key not in request_data:
            return False
        
        if isinstance(filter_value, dict):
            # Complex filter with operators
            operator = filter_value.get("operator", "equals")
            value = filter_value.get("value")
            
            request_value = request_data[filter_key]
            
            if operator == "equals" and request_value != value:
                return False
            elif operator == "contains" and value not in str(request_value):
                return False
            elif operator == "greater_than" and request_value <= value:
                return False
            elif operator == "less_than" and request_value >= value:
                return False
        else:
            # Simple equality check
            if request_data[filter_key] != filter_value:
                return False
    
    logger.info(f"API request trigger fired for {method} {endpoint}")
    return True


def handle_webhook_trigger(trigger_config: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
    """
    Handle webhook triggers
    
    Args:
        trigger_config: Trigger configuration with webhook filters
        event_data: Webhook event data
        
    Returns:
        True if trigger should fire based on webhook data
    """
    if not event_data:
        return False
    
    webhook_source = event_data.get("source", "")
    webhook_event = event_data.get("event_type", "")
    payload = event_data.get("payload", {})
    
    # Check webhook source filters
    allowed_sources = trigger_config.get("allowed_sources", [])
    if allowed_sources and webhook_source not in allowed_sources:
        return False
    
    # Check event type filters
    allowed_events = trigger_config.get("allowed_events", [])
    if allowed_events and webhook_event not in allowed_events:
        return False
    
    # Check payload filters
    payload_filters = trigger_config.get("payload_filters", {})
    for filter_path, filter_config in payload_filters.items():
        # Extract value from payload using dot notation
        payload_value = _get_nested_value(payload, filter_path)
        
        if not _evaluate_filter(payload_value, filter_config):
            return False
    
    # Check webhook signature validation
    if trigger_config.get("validate_signature", False):
        expected_signature = trigger_config.get("signature_header", "X-Signature")
        provided_signature = event_data.get("headers", {}).get(expected_signature)
        
        if not provided_signature:
            logger.warning("Webhook signature validation required but no signature provided")
            return False
        
        # In a real implementation, you would validate the signature
        # For now, we'll assume it's valid if present
    
    logger.info(f"Webhook trigger fired for {webhook_event} from {webhook_source}")
    return True


def handle_email_trigger(trigger_config: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
    """
    Handle email triggers
    
    Args:
        trigger_config: Trigger configuration with email filters
        event_data: Email event data
        
    Returns:
        True if trigger should fire based on email
    """
    if not event_data:
        return False
    
    sender = event_data.get("sender", "")
    subject = event_data.get("subject", "")
    body = event_data.get("body", "")
    recipients = event_data.get("recipients", [])
    
    # Check sender filters
    allowed_senders = trigger_config.get("allowed_senders", [])
    if allowed_senders:
        if not any(re.match(pattern, sender) for pattern in allowed_senders):
            return False
    
    # Check subject patterns
    subject_patterns = trigger_config.get("subject_patterns", [])
    if subject_patterns:
        if not any(re.search(pattern, subject, re.IGNORECASE) for pattern in subject_patterns):
            return False
    
    # Check body patterns
    body_patterns = trigger_config.get("body_patterns", [])
    if body_patterns:
        if not any(re.search(pattern, body, re.IGNORECASE) for pattern in body_patterns):
            return False
    
    # Check recipient filters
    required_recipients = trigger_config.get("required_recipients", [])
    if required_recipients:
        if not all(recipient in recipients for recipient in required_recipients):
            return False
    
    logger.info(f"Email trigger fired for email from {sender}")
    return True


# Helper functions

def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Get value from nested dictionary using dot notation"""
    keys = path.split('.')
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value


def _evaluate_filter(value: Any, filter_config: Dict[str, Any]) -> bool:
    """Evaluate a filter condition against a value"""
    if isinstance(filter_config, dict):
        operator = filter_config.get("operator", "equals")
        expected_value = filter_config.get("value")
        
        if operator == "equals":
            return value == expected_value
        elif operator == "not_equals":
            return value != expected_value
        elif operator == "contains":
            return expected_value in str(value)
        elif operator == "not_contains":
            return expected_value not in str(value)
        elif operator == "starts_with":
            return str(value).startswith(str(expected_value))
        elif operator == "ends_with":
            return str(value).endswith(str(expected_value))
        elif operator == "regex_match":
            return bool(re.match(str(expected_value), str(value)))
        elif operator == "greater_than":
            return value > expected_value
        elif operator == "less_than":
            return value < expected_value
        elif operator == "in":
            return value in expected_value
        elif operator == "not_in":
            return value not in expected_value
        else:
            return False
    else:
        # Simple equality check
        return value == filter_config


def create_trigger_evaluator(trigger_type: str) -> Optional[callable]:
    """
    Create a trigger evaluator function for the given trigger type
    
    Args:
        trigger_type: Type of trigger to create evaluator for
        
    Returns:
        Trigger evaluator function or None if type not supported
    """
    trigger_handlers = {
        "manual": handle_manual_trigger,
        "scheduled": handle_scheduled_trigger,
        "schema_change": handle_schema_change_trigger,
        "file_upload": handle_file_upload_trigger,
        "api_request": handle_api_request_trigger,
        "webhook": handle_webhook_trigger,
        "email": handle_email_trigger
    }
    
    return trigger_handlers.get(trigger_type)


def validate_trigger_config(trigger_type: str, config: Dict[str, Any]) -> List[str]:
    """
    Validate trigger configuration
    
    Args:
        trigger_type: Type of trigger
        config: Trigger configuration
        
    Returns:
        List of validation errors
    """
    errors = []
    
    if trigger_type == "scheduled":
        if "cron_expression" not in config:
            errors.append("Scheduled trigger requires 'cron_expression'")
        else:
            try:
                croniter.croniter(config["cron_expression"])
            except Exception as e:
                errors.append(f"Invalid cron expression: {e}")
    
    elif trigger_type == "schema_change":
        allowed_change_types = [
            "table_added", "table_removed", "column_added", "column_removed",
            "column_modified", "index_added", "index_removed"
        ]
        if "change_types" in config:
            invalid_types = [ct for ct in config["change_types"] if ct not in allowed_change_types]
            if invalid_types:
                errors.append(f"Invalid change types: {invalid_types}")
    
    elif trigger_type == "file_upload":
        if "allowed_extensions" in config:
            if not isinstance(config["allowed_extensions"], list):
                errors.append("'allowed_extensions' must be a list")
    
    elif trigger_type == "webhook":
        if config.get("validate_signature", False) and "signature_header" not in config:
            errors.append("Signature validation requires 'signature_header'")
    
    return errors
