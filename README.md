# RemindMe

This goal of this project is send yourself email reminders in the future ! You can forward/send an email to 1hour@yourdomain.com
and you will receive back your mail exactly one hour later.

## Features

You can send your reminder either to `delay@yourdomain.com` or add the delay in the subject of the email. To use the subject version, you need to setup a static address in the configuration file, let's say `remindme@yourdomain.com`, and add the delay enclosed by `[]` in the subject of your email.

Email version:

![alt text](https://github.com/valentinbonneaud/remindme/raw/master/images/8pm.png "Email version")

Subject version:

![alt text](https://github.com/valentinbonneaud/remindme/raw/master/images/remindme.png "Subject version")


### Delay

The following delays are supported:

- month
- week
- day
- hour
- min

### Exact timing

Exact hour is also supported by the server: `8am` or `4pm`.

### ProtonMail integration

You can use this project with your ProtonMail account and enjoy end-to-end encryption. It works by encrypting
 your reminder using the public key of your email (the email that you are using to send the email reminder). So when
 you will receive back your email, you and only you will be able to decrypt the reminder. The remote server
 operating this Python server will never be able to read your emails as the script don't have your GPG private key.

To do so, you first need to export your **public** key from the ProtonMail web client. Go to _Settings/Keys_, then click on the small arrow next to your email, it will open the GPG key view. From there, you can click on _Export_ and then _Public Key_. After having exported your public key, you can create a new contact, enter in the email field the email you added in the configuration file under _address_subject_. Once, the contact is saved, you can add your public key to the contact. To do so, open it and click on the _advanced settings_ icon next to the email. You can then import the public key you previously downloaded, in the modal and don't forget to activate encryption. And voilà ! All the reminders that you will send to your server will be encrypted.

## Basic installation

### Prerequesite

The basic DNS mail server configuration must be done (MX record) and is not covered in this file.

### Python prerequesites

Install all requirements using the following command `pip install -r requirements.txt`.

### Configuration file

All the configuration is located in the file `./config.yml`.

- `carbon_copies_path` (optional, default `./carbon_copies/`): Folder where a copy of all incoming mails are stored. If the setting is not provided, the email auto-saving will be disabled
- `queue_path` (default `./queue/`): Folder where the emails queued for sending are stored
- `timezone` (default `Europe/Paris`): Timezone used to interpret the exact hours (`8am` or `4pm`)
- `ip_bind` (default `127.0.0.1`): IP at which the SMTP server will be listening, can be your external or internal IP, if you are behind a NAT
- `port_bind` (default `25`): port at which the SMTP server will be listening
- `error_msg` (default `./back.eml`): default error mail, when the timing/hour received is invalid
- `address_subject` (optional, default `remindme@example.com`): static email used for the subject version (see Features)
- `authorized_from`  (list, default `- me@protonmail.com`): emails that are authorized to ask for reminders
- `allowed_ips`  (list, optional, default `- 127.0.0.1/32`): Restrict the SMTP IPs, the mail will be discarded if the SMTP IP is not in the list. If the setting is not provided, the filtering will be disabled
- `log_server` (default `./logs/server.log`): Path to the log file used by the incoming script
- `log_sender` (default `./logs/sender.log`): Path to the log file used by the outgoing script

## Run the server!

To start the scripts, you can use either the standard version which will run in the same process

- `python incoming_server.py`
- `python outgoing_server.py`

Or the daemon version

- `python incoming_server.py daemon`
- `python outgoing_server.py daemon`

To kill a daemon process, you can find the PID via the `ps -ax` and then `kill -9 pid`.