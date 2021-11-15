#!/usr/bin/env python3

import os
import sys
import time
import smtplib
from helper import *
from config import *
from ftplib import FTP
from pathlib import Path
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from smtplib import SMTP, SMTPException
from datetime import date, datetime, time
from email.mime.multipart import MIMEMultipart

EmailCount = 1


date = datetime.now().date()
time = datetime.now().time().strftime('%H:%M:%S')

# TODO add multi handling to attachment func


def get_file(site):
    """finds info for newest file to attach for %site"""
    newest_folder = Path('data/generated-feeds/%s/newest/' %
                         site)
    newest_feeds = newest_folder.iterdir()
    is_empty_dir = list_dir_ignore_hidden(newest_folder)
    if len(is_empty_dir):
        for item in newest_feeds:
            if item.is_file():
                attachment_name = item.name
                if attachment_name.endswith('.csv'):
                    attachment_path = "data/generated-feeds/%s/newest/%s" % (
                        site, attachment_name)
    else:
        print("\a\033[93mWarning: No files to attach! \n\t('%s/newest' directory is empty, please generate another feed or put one in manually)\n\033[0m" % site)
        sys.exit(1)
    return attachment_name, attachment_path


def ftp_connect(site):
    """Upload inventory files via FTP"""
    ftp_server = FTP(FTP_HOST)
    ftp_server.login(FTP_USER, FTP_PASSWORD)
    print("\n\033[92m\033[1mLOGGED IN:\033[00m %s@%s\n" % (FTP_USER, FTP_HOST))
    ftp_server.encoding = "utf-8"
    print("\n\033[92m\033[1mWELCOME MSG:\033[00m\n")
    print(ftp_server.getwelcome())
    print("\n\033[92m\033[1mDIRECTORIES:\033[00m\n")
    ftp_server.retrlines('LIST')
    print("\n\033[92m\033[1mCWD is:\033[00m %s\n" % ftp_server.pwd())
    print("Moving to %s..." % FTP_UPLOAD_DIR)
    ftp_server.cwd("%s" % FTP_UPLOAD_DIR)
    print("\n\033[92m\033[1mCWD is:\033[00m %s\n" % ftp_server.pwd())
    ftp_upload(site, ftp_server)
    ftp_server.quit()
    input("\a\n\033[96m🍻 *clink* Done! Hit 'Enter' to return to menu: \033[00m")


def ftp_upload(site, server):
    """Finds newest .csv file and uploads it to ftp server"""
    attachment = get_file(site)
    print("File %s will be uploaded to %s..." % (attachment[0], server.pwd()))
    up_okay = input('\nDo you want to upload this file? (y/N): ')
    if up_okay.lower() != 'y' or okay.lower() != 'yes':
        print("\n\033[91mOkay ¯\_(ツ)_/¯ Nothing will be done...\033[0m\n")
    else:
        with open(attachment[1], "rb") as file:
            '%s'.storbinary("STOR " + attachment[0], file) % server
            print("\tUpload Complete: %s >> %s" %
                  (attachment[0], server.pwd()))


def send_by_site(dic):
    """Send inventory emails to select sites"""
    print("Valid sites:")
    print_sites(dic)
    sites = sites_raw = []
    sites_raw = [item for item in input(
        "\nInput sites, seperated by space ('Enter' when done): ").split()]
    for site in sites_raw:  # remove bogus args
        if site in dic:
            sites.append(site.lower())
        else:
            print("\n\033[93m⚠️  Warning! No record of site '%s'...\033[00m\n\033[91m==> Removing '%s' from queue...\033[00m"
                  % (site, site))
    if len(sites) > 0:
        print("\n\033[96mGenerating emails for:\033[00m\n")
        sites_to_gen(sites, receiver_info)
        for site in sites:
            if len(sites) > 1:
                print(len(sites), "emails will be generated...")
                print("\033[92mGenerating your emails...\033[00m")
            else:
                print("1 email will be generated...")
                print("\033[92mGenerating your email...\033[00m\n")
            while EmailCount <= len(sites):
                print("""\n\033[92m########################################################################
# Email #%i/%i (%s)
# ---------------------------------------------------------------------\033[00m""" % (EmailCount, len(sites), site.upper()))
                gen_email(site)
                break
    else:
        input("\a\n😞 Nothing to do...hit 'Enter' to return to menu: \033[00m")
    input("\a\n\033[96m🍻 *clink* Done! Hit 'Enter' to return to menu: \033[00m")


def gen_email(site):
    """Generates email and shows preview"""
    receiver_email, greeting_name, site_name = receiver_info[
        site][0], receiver_info[site][2], receiver_info[site][1]
    mail_subj = "%s %s Inventory Feed for %s" % (date, our_company, site_name)
    msg = MIMEMultipart()  # start crafting msg
    msg['From'] = "%s<%s>" % (our_company, SENDER_EMAIL)
    msg['To'], msg['Subject'] = receiver_email, mail_subj
    # move_to_sent = email_attach(site, msg)  # attach csv
    newest_folder = Path('data/generated-feeds/%s/newest/' %
                         site)
    newest_feeds = newest_folder.iterdir()
    is_empty_dir = list_dir_ignore_hidden(newest_folder)
    if len(is_empty_dir):
        attachment_list = []
        for item in newest_feeds:
            if item.is_file():
                attachment_name = item.name
                if attachment_name.endswith('.csv'):
                    attachment_path = "data/generated-feeds/%s/newest/%s" % (
                        site, attachment_name)
                    # open and attach file
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(open(attachment_path, "rb").read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment',
                                    filename=attachment_name)
                    msg.attach(part)
                    attachment_list.append(attachment_name)
    else:
        print("\a\033[93mWarning: No files to attach! \n\t('%s/newest' directory is empty, please generate another feed or put one in manually)\n\033[0m" % site)
        sys.exit(1)
    if len(attachment_list) > 1:
        print("\n\033[92m\033[1mATTACHMENTS:\033[0m")
        for attachment in attachment_list:
            print(attachment)
    else:
        print("\n\033[92m\033[1mATTACHMENT:\n\033[0m%s \n(%s)" %
              (attachment_name, attachment_path))
    if not os.path.exists('data/generated-feeds/%s/sent' % site):
        os.makedirs('data/generated-feeds/%s/sent' % site)
    move_to_sent = "mv -v '%s' data/generated-feeds/%s/sent" % (
        attachment_path, site)
    # set email body text
    mail_body = "%s %s,\n\n%s\n\n%s\n%s" % (
        body_greeting, greeting_name, body_text, body_closer, our_company)
    # convert body to MIME compatible and attach
    mail_body = MIMEText(mail_body)
    msg.attach(mail_body)
    print("\033[92m\033[1mSEND TO:\n\033[0m%s (%s)\n\033[92m\033[1mSUBJECT:\n\033[0m%s\n\033[92m\033[1mBODY:\033[0m"
          % (greeting_name, receiver_email, mail_subj))  # preview crafted email data
    print(mail_body)
    print("""\n\033[92m#---------------------------------------------------------------------
# End of email
###################################################################### \033[00m""")
    send_email(msg, receiver_email, greeting_name, move_to_sent)


def send_email(msg, receiver_email, greeting_name, move_to_sent):
    """Sends generated emails upon approval, moving sent attachments >> `sent` upon completion"""
    send_okay = input('\nDo you want to send this email? (y/N): ')
    if send_okay.lower() != 'y':
        print("\n\033[91mOkay ¯\_(ツ)_/¯  No email will be sent...\033[0m\n")
        global EmailCount
        EmailCount += 1
    else:
        print("\n\033[96mOkay, let me warm up my fingers and...\033[0m")
        mail_to_send.sendmail(SENDER_EMAIL, receiver_email,
                              msg.as_string())  # sendit.exe
        print("\n\033[92mEmail successfully sent to %s (%s) at %s\033[0m\n" % (
            receiver_email, greeting_name, time))
        os.system(move_to_sent)  # move file to sent if attachment exists
        EmailCount += 1


def send_all():
    """Send inventory emails to all sites"""
    all_count = 1
    for key in receiver_info:
        while all_count <= len(receiver_info):
            print("""\n\033[92m#######################################################################
# Email #%i/%i
# ---------------------------------------------------------------------\033[00m""" % (all_count, len(receiver_info)))
            gen_email(key)
            all_count += 1
            break
    mail_to_send.quit()


# ---------------------------------------------------------------------
# The main event
# ---------------------------------------------------------------------

mail_to_send = smtplib.SMTP_SSL(
    SMTP_SERVER, SERVER_PORT)  # log in to email server
mail_to_send.ehlo()
mail_to_send.login(SENDER_EMAIL, EMAIL_PASSWORD)
