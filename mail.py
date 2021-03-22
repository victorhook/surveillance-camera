from email.mime.text import MIMEText
import json
import smtplib
import os


BASEDIR = os.path.dirname(os.path.abspath(__file__))


class MailHandler:

    PORT = 465
    SERVER = 'smtp.gmail.com'
    NAME = 'Weather-monitor'
    DEFAULT_SUBJECT = '[ Weather-monitor ]'

    def __init__(self, creds):
        self._creds = creds

    def send(self, body):
        server_ssl = smtplib.SMTP_SSL(MailHandler.SERVER, MailHandler.PORT)
        server_ssl.login(self._creds['username'], self._creds['password'])
        msg = self._create_message(body)
        server_ssl.send_message(msg)
        server_ssl.close()

    def _create_message(self, body):
        msg = MIMEText(body)
        msg['Subject'] = MailHandler.DEFAULT_SUBJECT
        msg['From'] = MailHandler.NAME
        msg['To'] = self._creds['recipient']
        return msg
