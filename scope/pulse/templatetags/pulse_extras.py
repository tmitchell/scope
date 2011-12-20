from datetime import datetime, timedelta

from django import template

register = template.Library()


class FormatTimelineNode(template.Node):
    """Displays a given timestamp if the day has changed, according to the specified format"""

    def __init__(self, timestamp, format_string):
        self.timestamp = template.Variable(timestamp)
        self.format_string = format_string

    def render(self, context):
        try:
            # reduce the timestamp to just year/month/date
            timestamp = self.timestamp.resolve(context)
            ymd_timestamp = datetime(year=timestamp.year, month=timestamp.month, day=timestamp.day)
            # see if the date we've gotten represents a new day for the timeline
            if self in context.render_context and ymd_timestamp <= context.render_context[self]:
                return ''
            context.render_context[self] = ymd_timestamp
            return ymd_timestamp.strftime(self.format_string)
        except template.VariableDoesNotExist:
            return ''


@register.tag(name='format_timeline')
def do_format_timeline(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, timestamp, format_string = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly two arguments" % token.contents.split()[0])
    if not (format_string[0] == format_string[-1] and format_string[0] in ('"', "'")):
        raise template.TemplateSyntaxError("%r tag's argument should be in quotes" % tag_name)
    return FormatTimelineNode(timestamp, format_string[1:-1])