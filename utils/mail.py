import os
import re
import time
from email.headerregistry import Address
from email.message import EmailMessage
from subprocess import Popen, PIPE
from typing import List, Tuple

from flask import current_app as app

_templates = {}

# noinspection RegExpRedundantEscape
_regex_html_param = re.compile(r"(\{\{[^}]+\}\})")


def _make_recipient_header(recipients):
    addresses = []
    for name, email in recipients:
        to_user, to_domain = email.split('@', 1)
        addresses.append(Address(name, to_user, to_domain))
    return addresses


def _send_mock_folder(msg, recipient_category, recipients, mock_folder):
    for name, email in recipients:
        folder = os.path.join(mock_folder, email)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(os.path.join(folder, '%f.txt' % time.time()), 'w') as f:
            f.write("From: %s\nSubject: %s\n%s: %s\n\n%s" % (str(msg['From']), msg['Subject'], recipient_category,
                                                             msg[recipient_category], msg.get_body('plain')))


class PreparedEmail:
    def __init__(self, msg, to_list: list, cc_list: list = None, bcc_list: list = None):
        self.msg = msg
        self.to_list = to_list
        self.cc_list = cc_list
        self.bcc_list = bcc_list

    def send(self):
        mock_folder = app.config['MAIL'].get('mock_folder')
        if mock_folder:
            if self.to_list:
                _send_mock_folder(self.msg, 'To', self.to_list, mock_folder)
            if self.cc_list:
                _send_mock_folder(self.msg, 'Cc', self.cc_list, mock_folder)
            if self.bcc_list:
                _send_mock_folder(self.msg, 'Bcc', self.bcc_list, mock_folder)
        else:
            p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
            p.communicate(self.msg.as_bytes())


def prepare_email(template: str, to_list: List[Tuple[str, str]], cc_list: List[Tuple[str, str]] = None,
                  bcc_list: List[Tuple[str, str]] = None, mail_args: dict = None):
    mail_config = app.config['MAIL']

    msg = EmailMessage()
    from_user, from_domain = mail_config['from'].split('@', 1)
    msg['From'] = Address(mail_config['display_name'], from_user, from_domain)

    reply_to_address = mail_config.get('reply_to')
    if reply_to_address:
        reply_to_user, reply_to_domain = reply_to_address.split('@', 1)
        reply_to_name = mail_config.get('reply_to_name') or ''
        msg['Reply-To'] = Address(reply_to_name, reply_to_user, reply_to_domain)

    if to_list:
        msg['To'] = _make_recipient_header(to_list)
    if cc_list:
        msg['Cc'] = _make_recipient_header(cc_list)
    if bcc_list:
        msg['Bcc'] = _make_recipient_header(bcc_list)

    temp = _templates.get(template)
    if temp is None:
        temp = {}
        txt_path = os.path.join('mail_templates', template + '.txt')
        html_path = os.path.join('mail_templates', template + '.html')
        with open(txt_path) as f_txt:
            txt = f_txt.read()
            temp['subject'], temp['text'] = txt.split('\n', 1)
        if os.path.isfile(html_path):
            with open(html_path) as f_html:
                temp['html'] = f_html.read()
        _templates[template] = temp

    temp_subject = temp['subject']
    temp_text = temp['text']
    temp_html = temp.get('html')

    if mail_args:
        temp_subject = temp_subject.format(**mail_args)
        temp_text = temp_text.format(**mail_args)
        if temp_html:
            # In html templates, double curly-braces are used for string interpolation to avoid conflict with css and js
            # functions
            temp_html = _regex_html_param.sub(lambda m: m.group(1)[1:-1].format(**mail_args), temp_html)

    msg['Subject'] = temp_subject
    msg.set_content(temp_text)
    if temp_html:
        msg.add_alternative(temp_html, subtype='html')

    return PreparedEmail(msg=msg, to_list=to_list, cc_list=cc_list, bcc_list=bcc_list)


def send_email(template: str, to_list: List[Tuple[str, str]], cc_list: List[Tuple[str, str]] = None,
               bcc_list: List[Tuple[str, str]] = None, mail_args: dict = None):
    mail = prepare_email(template, to_list, cc_list, bcc_list, mail_args)
    mail.send()
