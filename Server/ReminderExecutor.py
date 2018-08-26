import smtplib
import email.utils
import os
from os.path import isfile, join
from pytz import timezone
from datetime import datetime
from time import mktime
from Server.Logger import Logger
import dns.resolver
import re
from Server.Helper import Helper


class ReminderExecutor:

    def __init__(self, cfg):
        self.queue_path =  Helper.getElement(cfg, 'queue_path')
        self.timezone = Helper.getElement(cfg, 'timezone')
        self.logger = Logger(Helper.getElement(cfg, "log_outgoing"))

        self.logger.log_seperator('New Execution')
        self.logger.log('OK', 'ReminderExecutor created, reading ' + self.queue_path + ', timezone = ' + self.timezone)

    def getFiles(self):
        return [f for f in os.listdir(self.queue_path) if isfile(join(self.queue_path, f)) and f.endswith('.eml')]

    def getMX(self, email):
        regex = r"<([\w\.-_]*)@([\w\.-_]*)>"

        matches = re.search(regex, email)

        domain = None
        if matches:
            domain = matches.group(2)

        if domain is None:
            raise Exception("Domain of " + email + " not found.")

        self.logger.log('OK', 'Resolver: Resolving MX for ' + domain)

        data = {}
        for rdata in dns.resolver.query(domain, 'MX'):
            preference = rdata.preference
            if preference is None:
                preference = 1000

            self.logger.log('OK', 'Resolver: ' + str(rdata.exchange))
            data[preference] = str(rdata.exchange)

        min_preference = min(data.keys())
        return data[min_preference]

    def main(self):

        files = self.getFiles()
        unix_now = int(mktime(timezone(self.timezone).localize(datetime.now()).utctimetuple()))

        for mail in files:
            # we extract the timestamp from the filename
            timestamp = int(mail.split(".")[0])

            full_path = join(self.queue_path, mail)

            if timestamp <= unix_now:
                self.logger.log_seperator()
                self.logger.log('OK', 'New file: ' + mail)
                self.logger.log('OK', 'Extracted timestamp = ' + str(timestamp))
                self.logger.log('OK', 'It is time, we have to process it')

                content = ''
                with open(full_path, 'r') as f:
                    f.next()  # we skip the first line (received timestamp)
                    for line in f:
                        content += line

                msg = email.message_from_string(content)
                self.logger.log('OK', 'Sending ' + msg['Subject'])
                msg['Date'] = datetime.now().utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

                server_mx = self.getMX(msg['To'])
                self.logger.log('OK', 'Domain ' + msg['To'] + ' resolved to ' + server_mx)

                server = None
                try:

                    server = smtplib.SMTP(server_mx, 25)
                    server.set_debuglevel(True)  # show communication with the server
                    server.sendmail(msg['From'], [msg['To']], msg.__str__())
                    self.logger.log('OK', 'Message sent')
                    self.logger.log('OK', 'Deleting ' + full_path)
                    os.remove(full_path)
                    self.logger.log('OK', 'All good, finished.')
                except:
                    server.quit()
                    break
