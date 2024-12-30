# utils.py
import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def save_form_with_transaction(form, commit=True, extra_tags='success'):
    """
    Utility function to save form with transaction and return success or failure.
    """
    try:
        with transaction.atomic():
            instance = form.save(commit=commit)
        return instance, None
    except ValidationError as e:
        return None, f"Validation error: {e.message}"
    except Exception as e:
        logger.error(f"Error saving form: {str(e)}")
        return None, f"Error: {str(e)}"

def handle_error(request, message, extra_tags="danger"):
    """
    Utility function to handle error messages.
    """
    messages.error(request, message, extra_tags=extra_tags)
    logger.error(message)

def handle_success(request, message, extra_tags="success"):
    """
    Utility function to handle success messages.
    """
    messages.success(request, message, extra_tags=extra_tags)

def delete_instance_with_error_handling(request, instance, success_message, failure_message):
    """
    Utility function to delete an instance and handle success or failure.
    """
    try:
        instance.delete()
        handle_success(request, success_message)
    except Exception as e:
        handle_error(request, f"{failure_message}: {str(e)}")
