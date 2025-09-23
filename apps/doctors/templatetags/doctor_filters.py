from django import template

register = template.Library()

@register.filter
def filter_day(schedules, day_value):
    """Filter schedules by day of week"""
    return [schedule for schedule in schedules if schedule.day_of_week == day_value]
