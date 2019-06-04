import os
import smtplib
import time
from email.headerregistry import Address
from email.message import EmailMessage
from subprocess import Popen, PIPE
from typing import List, Tuple

from flask import current_app as app

from utils.message import MultiFormatMessageContent


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
        mail_config = app.config['MAIL']

        # use mock folder?
        mock_folder = mail_config.get('mock_folder')
        if mock_folder:
            if self.to_list:
                _send_mock_folder(self.msg, 'To', self.to_list, mock_folder)
            if self.cc_list:
                _send_mock_folder(self.msg, 'Cc', self.cc_list, mock_folder)
            if self.bcc_list:
                _send_mock_folder(self.msg, 'Bcc', self.bcc_list, mock_folder)
            return

        # use mail_catcher? (https://github.com/sj26/mailcatcher)
        mail_catcher_config = mail_config.get('mail_catcher')
        if mail_catcher_config:
            with smtplib.SMTP(host=mail_catcher_config.get('host'), port=mail_catcher_config.get('port')) as smtp:
                smtp.send_message(self.msg)
            return

        # use sendmail directly
        p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(self.msg.as_bytes())


def prepare_email(content: MultiFormatMessageContent, to_list: List[Tuple[str, str]],
                  cc_list: List[Tuple[str, str]] = None, bcc_list: List[Tuple[str, str]] = None):
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

    msg['Subject'] = content.subject
    msg.set_content(content.text)
    if content.email_html:
        msg.add_alternative(content.email_html, subtype='html')

    return PreparedEmail(msg=msg, to_list=to_list, cc_list=cc_list, bcc_list=bcc_list)


def send_email(content: MultiFormatMessageContent, to_list: List[Tuple[str, str]],
               cc_list: List[Tuple[str, str]] = None, bcc_list: List[Tuple[str, str]] = None):
    mail = prepare_email(content, to_list, cc_list, bcc_list)
    mail.send()
