import time, logging

from django import template
from django.conf import settings

logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def get_settings(name):
    return getattr(settings, name, "")
