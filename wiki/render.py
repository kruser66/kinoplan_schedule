"""Единственное место рендера markdown: его зовут страница статьи,
будущий превью-редактор и будущий API. Меняем настройки только здесь."""
import bleach
import markdown

_ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'ul', 'ol', 'li',
    'blockquote', 'strong', 'em', 'del', 'code', 'pre', 'hr', 'br',
    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'img',
]
_ALLOWED_ATTRS = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title'],
    'code': ['class'],
    'pre': ['class'],
    'th': ['align'],
    'td': ['align'],
}


def render_markdown(text):
    html = markdown.markdown(
        text or '',
        extensions=['tables', 'fenced_code', 'nl2br'],
    )
    return bleach.clean(html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True)
