import yaml.loader
from daemonize import Daemonize
from Server.ReminderExecutor import ReminderExecutor
import time
import sys

pid = '/tmp/mailsender.pid'
config_file = './config.yml'
app = 'outgoing_script'

def main():

    with open(config_file, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    executor = ReminderExecutor(cfg)

    while True:
        executor.main()
        time.sleep(5)


if len(sys.argv) > 1 and sys.argv[1] == "daemon":
    daemon = Daemonize(app=app, pid=pid, action=main)
    daemon.start()
else:
    main()