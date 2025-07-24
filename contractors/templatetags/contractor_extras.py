from django import template

register = template.Library()

@register.filter
def full_name(candidate):
    """
    Returns the full name (first_name + last_name) for a candidate object.
    Handles cases where first or last name might be None/empty.
    """
    first_name = candidate.contractor_first_name or ''
    last_name = candidate.contractor_last_name or ''
    
    # Concatenate with a space only if both parts exist
    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    elif last_name:
        return last_name
    return "" # Or return None, depending on desired behavior for no name