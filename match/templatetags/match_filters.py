from django import template

register = template.Library()

@register.filter
def get_other_user(match, current_user):
    """Get the other user in a match that is not the current user."""
    return match.users.exclude(id=current_user.id).first()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value 