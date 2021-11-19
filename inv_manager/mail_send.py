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
from datetime import date, datetime, time
from email.mime.multipart import MIMEMultipart
from helper import *
from config import cfg


SENDER_EMAIL = (cfg['sender_info']['SENDER_EMAIL'])
EMAIL_PASSWORD = (cfg['sender_info']['EMAIL_PASSWORD'])
SMTP_SERVER = (cfg['sender_info']['SMTP_SERVER'])
SERVER_PORT = (cfg['sender_info']['SERVER_PORT'])

FTP_HOST = (cfg['ftp_info']['FTP_HOST'])
FTP_USER = (cfg['ftp_info']['FTP_USER'])
FTP_PASSWORD = (cfg['ftp_info']['FTP_PASSWORD'])
FTP_UPLOAD_DIR = (cfg['ftp_info']['FTP_UPLOAD_PATH'])

our_company = (cfg['company_name'])
receiver_info = (cfg['receiver_info'])
body_greeting = (cfg['body_greeting'])
body_text = (cfg['body_text'])
body_closer = (cfg['body_closer'])

date = datetime.now().date()
time = datetime.now().time().strftime('%H:%M:%S')


def ftp_connect(site):
    """Upload inventory files via FTP"""
    ftp_server = FTP(FTP_HOST)
    ftp_server.login(FTP_USER, FTP_PASSWORD)
    print(f"\n\033[92m\033[1mLOGGED IN:\033[00m {FTP_USER}@{FTP_HOST}\n")
    ftp_server.encoding = "utf-8"
    print("\n\033[92m\033[1mWELCOME MSG:\033[00m\n")
    print(ftp_server.getwelcome())
    print("\n\033[92m\033[1mDIRECTORIES:\033[00m\n")
    ftp_server.retrlines('LIST')
    print(f"\n\033[92m\033[1mCWD is:\033[00m {ftp_server.pwd()}\n")
    print(f"Moving to {FTP_UPLOAD_DIR}...")
    ftp_server.cwd(f"{FTP_UPLOAD_DIR}")
    print(f"\n\033[92m\033[1mCWD is:\033[00m {ftp_server.pwd()}\n")
    ftp_upload(site, ftp_server)
    ftp_server.quit()
    input("\a\n\033[96m🍻 *clink* Done! Hit 'Enter' to return to menu: \033[00m")


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


def get_file(site):  # TODO squash and add multi handling
    """finds info for newest file to attach for site"""
    newest_folder = Path(f'data/generated-feeds/{site}/newest/')
    newest_feeds = newest_folder.iterdir()
    is_empty_dir = list_dir_ignore_hidden(newest_folder)
    if len(is_empty_dir):
        for item in newest_feeds:
            if item.is_file():
                attachment_name = item.name
                if attachment_name.endswith('.csv'):
                    attachment_path = f'data/generated-feeds/{site}/newest/{attachment_name}'
    else:
        print(
            f"\a\033[93mWarning: No files to attach! \n\t('{site}/newest' directory is empty, please generate another feed or put one in manually)\n\033[0m")
        sys.exit(1)
    return attachment_name, attachment_path


def send_by_site(dic):
    """Send inventory emails to select sites"""
    print("Valid sites:")
    print_sites(dic)
    sites = sites_raw = []
    sites_raw = input(
        "\nInput sites, seperated by space ('Enter' when done): ").split()
    for site in sites_raw:  # remove bogus input
        if site in dic:
            sites.append(site.lower())
        else:
            print(
                f"\n\033[93m⚠️  Warning! No record of site '{site}'...\033[00m\n\033[91m==> Removing '{site}' from queue...\033[00m")
    if sites:
        print("\n\033[96mGenerating emails for:\033[00m\n")
        sites_to_gen(sites, receiver_info)
        for site in sites:
            if len(sites) > 1:
                print(f"{len(sites)} emails will be generated...")
                print("\033[92mGenerating your emails...\033[00m")
            else:
                print("1 email will be generated...")
                print("\033[92mGenerating your email...\033[00m\n")
        count = 1
        create_emails(count, sites)
    else:
        input("\a\n😞 Nothing to do...hit 'Enter' to return to menu: \033[00m")
    input("\a\n\033[96m🍻 *clink* Done! Hit 'Enter' to return to menu: \033[00m")


def create_emails(count, sites):
    for site in sites:
        while count <= len(sites):
            print(f"""\n\033[92m#######################################################################
# Email #{count}/{len(sites)} ({site.upper()})
# ---------------------------------------------------------------------\033[00m""")
            gen_email(site)
            count += 1
            break


def gen_email(site):
    """Generates email and shows preview"""
    receiver_email, greeting_name, site_name = receiver_info[
        site][0], receiver_info[site][2], receiver_info[site][1]
    mail_subj = f"{date} {our_company} Inventory Feed for {site_name}"
    msg = MIMEMultipart()  # start crafting msg
    msg['From'] = f"{our_company}<{SENDER_EMAIL}>"
    msg['To'], msg['Subject'] = receiver_email, mail_subj
    newest_folder = Path(f'data/generated-feeds/{site}/newest/')
    newest_feeds = newest_folder.iterdir()
    is_empty_dir = list_dir_ignore_hidden(newest_folder)
    if len(is_empty_dir):
        attachment_list = []  # for multiple files
        for item in newest_feeds:
            if item.is_file():
                attachment_name = item.name
                if attachment_name.endswith('.csv'):
                    attachment_path = f'data/generated-feeds/{site}/newest/{attachment_name}'
                    # open and attach file
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(open(attachment_path, "rb").read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment',
                                    filename=attachment_name)
                    msg.attach(part)
                    attachment_list.append(attachment_name)
    else:
        print(
            "\a\033[93mWarning: No files to attach! \n\t('{site}/newest' directory is empty, please generate another feed or put one in manually)\n\033[0m")
        sys.exit(1)
    if len(attachment_list) > 1:
        print("\n\033[92m\033[1mATTACHMENTS:\033[0m")
        for attachment in attachment_list:
            print(attachment)
    else:
        print(
            f'\n\033[92m\033[1mATTACHMENT:\n\033[0m{attachment_name} \n({attachment_path})')
    if not os.path.exists(f'data/generated-feeds/{site}/sent'):
        os.makedirs(f'data/generated-feeds/{site}/sent')
    move_to_sent = f"mv -v '{attachment_path}' data/generated-feeds/{site}/sent"
    # set body text
    mail_body = f"{body_greeting} {greeting_name},\n\n{body_text}\n\n{body_closer}\n{our_company}"
    mail_body = MIMEText(mail_body)  # MIME it and attach
    msg.attach(mail_body)
    # preview crafted email data
    print(
        f'\033[92m\033[1mSEND TO:\n\033[0m{greeting_name} ({receiver_email})\n\033[92m\033[1mSUBJECT:\n\033[0m{mail_subj}\n\033[92m\033[1mBODY:\033[0m')
    print(mail_body)
    print("""\n\033[92m#---------------------------------------------------------------------
# End of email
######################################################################## \033[00m""")
    send_email(msg, receiver_email, greeting_name, move_to_sent)


def send_email(msg, receiver_email, greeting_name, move_to_sent):
    """Sends generated emails upon approval, moving sent attachments to `sent` upon completion"""
    send_okay = input('\nDo you want to send this email? (y/N): ')
    if send_okay.lower() != 'y':
        print("\n\033[91mOkay, no email will be sent...\033[0m\n")
    else:
        print("\n\033[96mOkay, let me warm up my fingers and...\033[0m")
        mail_to_send.sendmail(SENDER_EMAIL, receiver_email,
                              msg.as_string())  # sendit.exe
        print(
            f"\n\033[92mEmail successfully sent to {receiver_email} ({greeting_name}) at {time}\033[0m\n")
        os.system(move_to_sent)  # move file to sent if attachment exists


def send_all():
    """Send inventory emails to all sites"""
    count = 1
    create_emails(count, receiver_info)
    mail_to_send.quit()

# ---------------------------------------------------------------------
# The main event
# ---------------------------------------------------------------------


mail_to_send = smtplib.SMTP_SSL(
    SMTP_SERVER, SERVER_PORT)  # log in to email server
mail_to_send.ehlo()
mail_to_send.login(SENDER_EMAIL, EMAIL_PASSWORD)
