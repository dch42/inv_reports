#!/usr/bin/env python3

import os
import sys
import time
import smtplib
from ftplib import FTP
from pathlib import Path
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, time
import helper as h
from config import cfg

SENDER_EMAIL = (cfg['sender_info']['SENDER_EMAIL'])
EMAIL_PASSWORD = (cfg['sender_info']['EMAIL_PASSWORD'])
SMTP_SERVER = (cfg['sender_info']['SMTP_SERVER'])
SERVER_PORT = (cfg['sender_info']['SERVER_PORT'])

our_company = (cfg['company_name'])
receiver_info = (cfg['receiver_info'])
body_greeting = (cfg['body_greeting'])
body_text = (cfg['body_text'])
body_closer = (cfg['body_closer'])

date = datetime.now().date()
time = datetime.now().time().strftime('%H:%M:%S')

DASHES = 68*'-'
HASHES = 70*'#'


def ftp_connect():
    """Upload inventory files via FTP"""
    sites = h.validate_sites((cfg['ftp_info']))
    for site in sites:
        ftp_host = (cfg['ftp_info'][f'{site}']['FTP_HOST'])
        ftp_user = (cfg['ftp_info'][f'{site}']['FTP_USER'])
        ftp_password = (cfg['ftp_info'][f'{site}']['FTP_PASSWORD'])
        ftp_upload_dir = (cfg['ftp_info'][f'{site}']['FTP_UPLOAD_PATH'])
        ftp_server = FTP(ftp_host)
        ftp_server.login(ftp_user, ftp_password)
        print(f"\n\033[92m\033[1mLOGGED IN:\033[00m {ftp_user}@{ftp_host}\n")
        ftp_server.encoding = "utf-8"
        print("\n\033[92m\033[1mWELCOME MSG:\033[00m\n")
        print(ftp_server.getwelcome())
        print("\n\033[92m\033[1mDIRECTORIES:\033[00m\n")
        ftp_server.retrlines('LIST')
        print(f"\n\033[92m\033[1mCWD is:\033[00m {ftp_server.pwd()}\n")
        print(f"Moving to {ftp_upload_dir}...")
        ftp_server.cwd(f"{ftp_upload_dir}")
        print(f"\n\033[92m\033[1mCWD is:\033[00m {ftp_server.pwd()}\n")
        ftp_upload(site, ftp_server)
        ftp_server.quit()
        h.cheers()


def ftp_upload(site, server):
    """Finds newest .csv file and uploads it to ftp server"""
    attachment = get_file(site)
    print(f"File {attachment[0]} will be uploaded to {server.pwd()}...")
    up_ok = input('\nDo you want to upload this file? (y/N): ')
    if up_ok.lower() != 'y' or up_ok.lower() != 'yes':
        print("\n\033[91mOkay, nothing will be done...\033[0m\n")
    else:
        with open(attachment[1], "rb") as file:
            f'{server}'.storbinary("STOR " + attachment[0], file)
            print(f"\tUpload Complete: {attachment[0]} >> {server.pwd()}")


def init_mail():
    """Log in to email server"""
    try:
        mail_to_send = smtplib.SMTP_SSL(
            SMTP_SERVER, SERVER_PORT)
        mail_to_send.ehlo()
        mail_to_send.login(SENDER_EMAIL, EMAIL_PASSWORD)
        print(
            f"\n\033[92m[SUCCESS]\033[0m: \033[96m\033[5m📧 \033[0m\033[0mLogged in as \
{SENDER_EMAIL} to {SMTP_SERVER} on port {SERVER_PORT}...\n")
    except Exception as error:
        print(f"\a\n\033[91m[ERROR]: {error}\033[0m\n")
        input(
            "😞 Connection failed.\
                \n\nMaybe inspecting `Email Account Info` in config file will help?\
                \n\nPress `ENTER` to edit config file or `CTRL+C` to quit...")
        os.system("nano ../config/config.yml")
        sys.exit(1)
    return mail_to_send


def send_by_site():
    """Send inventory emails to select sites"""
    mail_to_send = init_mail()
    sites = h.validate_sites(receiver_info)
    if sites:
        print("\n\033[96mGenerating emails for:\033[00m\n")
        h.sites_to_gen(sites, receiver_info)
        if len(sites) > 1:
            print(f"{len(sites)} emails will be generated...")
            print("\033[92mGenerating your emails...\033[00m")
        else:
            print("1 email will be generated...")
            print("\033[92mGenerating your email...\033[00m\n")
        count = 1
        create_emails(count, sites, mail_to_send)
        mail_to_send.quit()
        h.cheers()
    else:
        h.nothing_to_do()


def create_emails(count, sites, mail_to_send):
    """Begin email creation loop"""
    for site in sites:
        while count <= len(sites):
            white_space = (
                69-(13+len(str(count))+len(str(len(sites)))+len(site)))*" "
            print(
                f"\n\033[92m{HASHES}\
                    \n# Email #{count}/{len(sites)} ({site.upper()}){white_space}#\
                \n#{DASHES}#\033[00m")
            gen_email(site, mail_to_send)
            count += 1
            break


def gen_email(site, mail_to_send):
    """Generates email and shows preview"""
    receiver_email, greeting_name, site_name = receiver_info[
        site][0], receiver_info[site][2], receiver_info[site][1]
    mail_subj = f"{date} {our_company} Inventory Feed for {site_name}"
    msg = MIMEMultipart()  # start crafting msg
    msg['From'] = f"{our_company}<{SENDER_EMAIL}>"
    msg['To'], msg['Subject'] = receiver_email, mail_subj
    attachment = get_file(site, msg, email=True)
    msg = attachment[3]
    if len(attachment[2]) > 1:
        print("\n\033[92m\033[1mATTACHMENTS:\033[0m")
        for item in attachment[2]:
            print(item)
    else:
        print(
            f'\n\033[92m\033[1mATTACHMENT:\n\033[0m{attachment[0]} \n({attachment[1]})')

    # set body text
    mail_body = f"{body_greeting} {greeting_name},\n\n{body_text}\n\n{body_closer}\n{our_company}"
    mail_body = MIMEText(mail_body)  # MIME it and attach
    msg.attach(mail_body)
    # preview crafted email data
    print(
        f'\033[92m\033[1mSEND TO:\n\033[0m{greeting_name} ({receiver_email})\
            \n\033[92m\033[1mSUBJECT:\n\033[0m{mail_subj}\
            \n\033[92m\033[1mBODY:\033[0m')
    print(mail_body)
    print(f"\n\033[92m#{DASHES}#\n# End of email" +
          55*" "+f"#\n{HASHES}\033[00m")
    send_email(msg, receiver_email, greeting_name,
               attachment, mail_to_send, site)


def get_file(site, msg=False, email=False):
    """finds info for newest file to attach for site"""
    attachment_list = []  # for multiple files
    newest_folder = Path(f'data/generated-feeds/{site}/newest/')
    newest_feeds = newest_folder.iterdir()
    is_empty_dir = h.list_dir_ignore_hidden(newest_folder)
    if len(is_empty_dir):
        for item in newest_feeds:
            if item.is_file():
                attachment_name = item.name
                if attachment_name.endswith('.csv'):
                    attachment_path = f'data/generated-feeds/{site}/newest/{attachment_name}'
                    if email:
                        with open(attachment_path, 'rb') as file:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(file.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition',
                                            'attachment', filename=attachment_name)
                            msg.attach(part)
                            attachment_list.append(attachment_name)

    else:
        print(
            f"\a\033[93m⚠️  Warning: No files to attach! \
                \n\t('{site}/newest' directory is empty, please generate another feed \
or put one in manually)\n\033[0m")
        sys.exit(1)
    return attachment_name, attachment_path, attachment_list, msg


def send_email(msg, receiver_email, greeting_name, attachment, mail_to_send, site):
    """Sends generated emails upon approval, moving sent attachments to `sent` upon completion"""
    send_okay = input('\nDo you want to send this email? (y/N): ')
    if send_okay.lower() != 'y':
        print("\n\033[91mOkay, no email will be sent...\033[0m\n")
    else:
        print("\n\033[96mOkay, let me warm up my fingers and...\033[0m")
        mail_to_send.sendmail(SENDER_EMAIL, receiver_email,
                              msg.as_string())  # sendit.exe
        print(
            f"\n\033[92mEmail successfully sent to {receiver_email} ({greeting_name}) \
at {time}\033[0m\n")
        for item in attachment[2]:
            h.sort_files(site, 'sent', 'generated-feeds', item, 'newest')


def send_all():
    """Send inventory emails to all sites"""
    mail_to_send = init_mail()
    count = 1
    create_emails(count, receiver_info, mail_to_send)
    mail_to_send.quit()
