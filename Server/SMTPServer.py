from __future__ import unicode_literals
import smtpd
import email
import re
from pytz import timezone
from datetime import datetime, timedelta
from time import mktime
from os import path
from random import randint
import ipaddress
from Server.Logger import Logger
from Server.Helper import Helper


class SMTPServer(smtpd.SMTPServer):

    args = ["month", "week", "day", "hour", "min", "am", "pm"]

    def __init__(self, cfg):
        self.carbon_copies_path = Helper.getElement(cfg, 'carbon_copies_path', optional=True)
        self.queue_path = Helper.getElement(cfg, 'queue_path')
        self.timezone = Helper.getElement(cfg, 'timezone')
        self.authorized_from = Helper.getElement(cfg, 'authorized_from')
        self.allowed_ip = Helper.getElement(cfg, 'allowed_ips')
        self.error_msg = Helper.getElement(cfg, 'error_msg')
        self.address_subject = Helper.getElement(cfg, 'address_subject', optional=True)
        self.logger = Logger(Helper.getElement(cfg, "log_ingoing"))

        local_address = (
            Helper.getElement(cfg, 'ip_bind'),
            Helper.getElement(cfg, 'port_bind')
        )

        smtpd.SMTPServer.__init__(self, localaddr=local_address, remoteaddr=None)
        self.logger.log_seperator('New Execution')
        self.logger.log('OK', 'Server created at (' + str(cfg['ip_bind']) + ', ' + str(cfg['port_bind']) + ')')

    def writeMail(self, msg, timestamp):
        filename = self.queue_path + str(timestamp) + '.' + str(randint(0, 999999)) + '.eml'
        if not path.isfile(filename):
            f = open(filename, "w")
            f.write(msg.__str__())
            f.close()
            self.logger.log('OK', "File " + filename + " created")

    def logEndRequest(self):
        self.logger.log_seperator('End of request')

    def loadMail(self, filename):
        content = ''
        with open(filename, 'r') as f:
            f.next()  # we skip the first line (received timestamp)
            for line in f:
                content += line

        return email.message_from_string(content)

    def isInt(self, i):
        try:
            int(i)
            return True
        except ValueError:
            return False

    def saveMail(self, peer, mailfrom, rcpttos, msg):
        t = int(mktime(timezone(self.timezone).localize(datetime.now()).utctimetuple()))
        name = self.carbon_copies_path + str(t) + '_' + mailfrom + '_' + rcpttos[0] + '_' + peer[0] + '.eml'
        f = open(name, "w")
        f.write(msg.__str__())
        f.close()

    def process_message(self, peer, mailfrom, rcpttos, data):
        self.logger.log('OK', 'Receiving message from: (' + str(peer[0]) + ', ' + str(peer[1]) + ')')
        ip_from = peer[0]

        msg = email.message_from_string(data)

        if self.carbon_copies_path is not None:
            self.saveMail(peer, mailfrom, rcpttos, msg)

        allowed = False
        for subnet in self.allowed_ip:
            if ipaddress.ip_address(unicode(ip_from, "utf-8")) in ipaddress.ip_network(unicode(subnet, "utf-8")):
                allowed = True
                break

        if not allowed:
            self.logger.log('WARNING', 'IP SMTP not authorized, aborting...')
            self.logEndRequest()
            return

        self.logger.log('OK', 'Message addressed from:' + mailfrom)

        if mailfrom not in self.authorized_from:
            self.logger.log('WARNING', 'Not authorized, aborting...')
            self.logEndRequest()
            return

        self.logger.log('OK', 'Message addressed to  :' + ', '.join(rcpttos))
        self.logger.log('OK', 'Message from          :' + msg['From'])

        ## check spoofing

        if not msg['From'].find("<" + mailfrom + ">") >= 0:
            self.logger.log('WARNING', 'Spoofing, aborting...')
            self.logEndRequest()
            return

        # get the delay
        if self.address_subject is not None and rcpttos[0].find(self.address_subject) >= 0:
            # get it from the subject
            data_delay = msg['Subject']
            regex = r"\[([+-]{0,1}\d+)(" + "|".join(self.args) + ")\]"
        else:
            data_delay = rcpttos[0]
            regex = r"([+-]{0,1}\d+)(" + "|".join(self.args) + ")"

        self.logger.log('OK', 'Matching: ' + data_delay + ' with regex ' + regex)

        # we extract the delay
        matches = re.search(regex, data_delay)
        digit = ""
        argument = ""

        if matches:
            self.logger.log('OK', "Match was found at {start}-{end}: {match}".format(
                start=matches.start(), end=matches.end(), match=matches.group()))

            if len(matches.groups()) == 2:
                digit = matches.group(1)
                argument = matches.group(2)

        if not self.isInt(digit) or argument not in self.args:
            self.logger.log('WARNING', 'Error parsing to address')
            self.logEndRequest()
            return

        digit_int = int(digit)

        current_date = datetime.now()
        send_at = 0

        if argument == "month":
            send_at = current_date + timedelta(digit_int * 31)
        elif argument == "week":
            send_at = current_date + timedelta(digit_int * 7)
        elif argument == "day":
            send_at = current_date + timedelta(digit_int)
        elif argument == "hour":
            send_at = current_date + timedelta(0, digit_int * 3600)
        if argument == "min":
            send_at = current_date + timedelta(0, digit_int * 60)
        elif argument == "am":
            send_at = current_date.replace(hour=digit_int, minute=0, second=0)
            if send_at < current_date:
                send_at = send_at + timedelta(1)
        elif argument == "pm":
            send_at = current_date.replace(hour=(12+digit_int), minute=0, second=0)
            if send_at < current_date:
                send_at = send_at + timedelta(1)

        if send_at == 0 or digit_int < 0:
            self.logger.log('WARNING', 'Error parsing the date')
            self.logger.log('WARNING', 'Sending the error message at timestamp 0')

            # we load the stored error message and overwrite some needed fields
            error_msg = self.loadMail(self.error_msg)
            error_msg['To'] = mailfrom + " <" + mailfrom + ">"
            error_msg['Subject'] = msg['Subject']
            error_msg['Message-ID'] = msg['Message-ID']
            error_msg['Feedback-ID'] = msg['Feedback-ID']

            # send the message ASAP
            self.writeMail(error_msg, 0)
            self.logEndRequest()

            return

        timestamp = int(mktime(timezone(self.timezone).localize(send_at).utctimetuple()))

        self.logger.log('OK', 'Delay is' + str(digit) + 'and arg =' + argument + ', we will send back at ' + str(send_at) + '(timestamp = ' + str(timestamp) + ')')
        self.logger.log('OK', 'Message length        :' + str(len(data)))

        for part in msg.walk():
            # each part is a either non-multipart, or another multipart message
            # that contains further parts... Message is organized like a tree
            if part.get_content_type() == 'text/plain':
                print part.get_payload()  # prints the raw text

        # we delete email specific related fields
        del msg['Date']
        del msg['DKIM-Signature']
        del msg['Reply-To']
        del msg['X-Spam-Status']
        del msg['X-Spam-Checker-Version']

        del msg['To']
        msg['To'] = mailfrom + " <" + mailfrom + ">"
        del msg['From']
        msg['From'] = rcpttos[0]

        self.writeMail(msg, timestamp)

        self.logEndRequest()
        return
