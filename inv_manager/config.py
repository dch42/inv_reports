import yaml

with open('../config/config.yml', 'r') as stream:
    try:
        cfg = (yaml.safe_load(stream))
    except Exception as e:
        print(e)

qb_path = (cfg['path_to_qb'])

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
brand_list = (cfg['brand_list'])

backorder_site_list = (cfg['backorder_site_list'])
backorder_cols = (cfg['backorder_cols'])
discontinued_cols = (cfg['discontinued_cols'])
months_out = (cfg['months'])

body_greeting = (cfg['body_greeting'])
body_text = (cfg['body_text'])
body_closer = (cfg['body_closer'])

site_dic = (cfg['site_dic'])
rearrange_dic = (cfg['rearrange_dic'])
