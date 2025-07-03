from django import template

register = template.Library()



@register.filter
def multiply(qty, price):
    
    
    return qty * price
    


@register.filter
def add_float(value, arg):
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return value