import asyncore
import yaml.loader
from daemonize import Daemonize
from Server.SMTPServer import SMTPServer
import sys

pid = '/tmp/mailserver.pid'
config_file = './config.yml'
app = 'incoming_script'


def main():
    with open(config_file, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    server = SMTPServer(cfg)
    asyncore.loop()


if len(sys.argv) > 1 and sys.argv[1] == "daemon":
    daemon = Daemonize(app=app, pid=pid, action=main)
    daemon.start()
else:
    main()
