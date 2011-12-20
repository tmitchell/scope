from datetime import datetime, timedelta

from django import template

register = template.Library()


class GetDailyTimestampNode(template.Node):
    """Stores a given timestamp if the day has changed"""

    def __init__(self, timestamp, context_var_name):
        self.timestamp = template.Variable(timestamp)
        self.context_var_name = context_var_name

    def render(self, context):
        context[self.context_var_name] = ''
        try:
            # reduce the timestamp to just year/month/date
            timestamp = self.timestamp.resolve(context)
            ymd_timestamp = datetime(year=timestamp.year, month=timestamp.month, day=timestamp.day)
            # see if the date we've gotten represents a new day for the timeline
            if self in context.render_context and ymd_timestamp <= context.render_context[self]:
                return ''
            context.render_context[self] = ymd_timestamp
            context[self.context_var_name] = ymd_timestamp
            return ''
        except template.VariableDoesNotExist:
            return ''


@register.tag(name='get_daily_timestamp')
def get_daily_timestamp(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, timestamp, as_string, context_var_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly three arguments" % token.contents.split()[0])
    if as_string != 'as':
        raise template.TemplateSyntaxError("Usage: %s timestamp as varname" % tag_name)
    if context_var_name[0] == context_var_name[-1] and context_var_name[0] in ('"', "'"):
        raise template.TemplateSyntaxError("%r tag's varname argument should not be in quotes" % tag_name)
    return GetDailyTimestampNode(timestamp, context_var_name)