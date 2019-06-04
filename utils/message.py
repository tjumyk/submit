import os
import re

MSG_TEMPLATES_DIR = 'mail_templates'

_templates = {}

# noinspection RegExpRedundantEscape
_regex_html_param = re.compile(r"\{\{([^}]+)\}\}")


class MultiFormatMessageContent:
    def __init__(self, subject: str, text: str, email_html: str, site_html: str):
        self.subject = subject
        self.text = text
        self.email_html = email_html
        self.site_html = site_html


def _build_html_message(template_html: str, args: dict):
    # In html templates, double curly-braces are used for string interpolation to avoid conflict with css and js
    # functions
    return _regex_html_param.sub(lambda m: ('{%s}' % m.group(1).strip()).format(**args), template_html)


def build_message_with_template(template: str, args: dict = None) -> MultiFormatMessageContent:
    temp = _templates.get(template)
    if temp is None:
        temp = {}
        txt_path = os.path.join(MSG_TEMPLATES_DIR, template + '.txt')
        email_html_path = os.path.join(MSG_TEMPLATES_DIR, template + '.html')
        site_html_path = os.path.join(MSG_TEMPLATES_DIR, template + '.site.html')
        with open(txt_path) as f_txt:  # txt is mandatory
            txt = f_txt.read()
            temp['subject'], temp['text'] = txt.split('\n', 1)
        if os.path.isfile(email_html_path):  # email html is optional
            with open(email_html_path) as f_email_html:
                temp['email_html'] = f_email_html.read()
        if os.path.isfile(site_html_path):  # site html is optional
            with open(site_html_path) as f_site_html:
                temp['site_html'] = f_site_html.read()
        _templates[template] = temp

    subject = temp['subject']
    text = temp['text']
    email_html = temp.get('email_html')
    site_html = temp.get('site_html')

    if args:
        subject = subject.format(**args)
        text = text.format(**args)
        if email_html:
            email_html = _build_html_message(email_html, args)
        if site_html:
            site_html = _build_html_message(site_html, args)

    return MultiFormatMessageContent(subject=subject, text=text, email_html=email_html, site_html=site_html)


def build_message_with_text(subject: str, text: str) -> MultiFormatMessageContent:
    content = build_message_with_template('default', {'content': text})
    content.subject = subject
    return content
