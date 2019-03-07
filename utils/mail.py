import os
import re
import time
from email.headerregistry import Address
from email.message import EmailMessage
from subprocess import Popen, PIPE

from flask import current_app as app

_templates = {}


def send_email(to_name, to_email, template, **kwargs):
    send_emails([(to_name, to_email)], template, **kwargs)


def send_emails(to_list, template, **kwargs):
    mail_config = app.config['MAIL']

    msg = EmailMessage()
    from_user, from_domain = mail_config['from'].split('@', 1)
    msg['From'] = Address(mail_config['display_name'], from_user, from_domain)
    to_addresses = []
    for name, email in to_list:
        to_user, to_domain = email.split('@', 1)
        to_addresses.append(Address(name, to_user, to_domain))
    msg['To'] = to_addresses

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

    msg['Subject'] = temp['subject'].format(**kwargs)
    msg.set_content(temp['text'].format(**kwargs))
    temp_html = temp.get('html')
    if temp_html:
        # In html templates, double curly-braces are used for string interpolation to avoid conflict with css and js
        # functions
        html = re.sub(r"(\{\{[^}]+\}\})", lambda m: m.group(1)[1:-1].format(**kwargs), temp_html)
        msg.add_alternative(html, subtype='html')

    mock_folder = app.config['MAIL'].get('mock_folder')
    if mock_folder:
        for name, email in to_list:
            folder = os.path.join(mock_folder, email)
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with open(os.path.join(folder, '%f.txt' % time.time()), 'w') as f:
                f.write("From: %s\nSubject: %s\n\n%s" % (str(msg['From']), msg['Subject'], msg.get_body()))
    else:
        p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(msg.as_bytes())
