import datetime


class Logger:

    def __init__(self, log_file):
        self.file = log_file

    def log_seperator(self, state=""):
        self.log("OK", '------------' + state + '------------')

    def log(self, status, message):
        msg = str(datetime.datetime.now()) + " - " + status + " - " + message
        print msg

        if self.file is not None:
            f = open(self.file, "a")
            f.write(msg + "\r\n")
            f.close()
