#!/usr/bin/env python3

import os
import sys
import time
import pyfiglet
import numpy as np
import pandas as pd
from config import *
from helper import *
from mail_send import *
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

date = datetime.now().date()
time = datetime.now().time().strftime('%H-%M-%S')

progver = "1.1"


def menu_loop(menu, qb_path):
    """Persistant modular menu boi"""
    choice = None
    while choice != 'q':
        os.system("clear")
        if menu == gen_menu:
            title = "Feed Generator"
        elif menu == email_menu:
            title = "Send Feeds"
        else:
            title = "Inv-Manager"
        pyfiglet.print_figlet("%s" % title)
        print("QB path: '%s'" % qb_path)
        print("Logged in as %s to %s on port %s...\n" %
              (SENDER_EMAIL, SMTP_SERVER, SERVER_PORT))
        print("Ver.", progver)
        print("Pandas version: " + pd.__version__)
        print("Numpy version: " + np.__version__)
        print("\n\033[92mCreate and send updated inventory feed csv files to dropship portals.\n\n\tThe new feeds are saved in `data/generated-feeds`.\n\tThe templates are stored in `data/inventory-templates`.\033[00m\n")
        print("""\n\033[1m#---------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------\033[0m\n""")
        for key, value in menu.items():
            print('\033[96m%s:\033[0m \033[95m%s\033[0m' %
                  (value[2], value[0].__doc__))
        print("\033[96m(q)uit/back\033[0m")
        print(
            """\n\033[1m#---------------------------------------------------------------------\033[0m\n""")
        choice = input('\nAction?: ').lower().strip()
        if choice in menu:
            menu[choice][1]()


def gen_feed_menu(qb_path):
    """Generate inventory feeds"""
    menu_loop(gen_menu, qb_path)


def send_email_menu():
    """Send inventory feeds"""
    menu_loop(email_menu, qb_path)


def import_qb(qb_path):
    """Import data from QB"""
    qb_df = pd.read_csv(qb_path, sep=",", encoding="Latin-1",
                        usecols=['Item', 'Quantity On Hand'])
    qb_df['Item'] = qb_df['Item'].astype(str)
    qb_df = qb_df.replace({'(m-)': ''}, regex=True)  # sanitization zone
    print("\nQB Import Complete: %s\n" % qb_path)
    return qb_df


def gen_by_site(site_dic, backorder_site_list):
    """Generate feeds for specific sites"""
    print("Valid sites:")
    print_sites(site_dic)
    sites = sites_raw = []
    sites_raw = [item for item in input(
        "\nInput sites, seperated by space ('Enter' when done): ").split()]
    for site in sites_raw:  # remove bogus input
        if site in site_dic:
            sites.append(site)
        else:
            print("\n\033[93m⚠️  Warning! No record of site '%s'...\033[00m\n\033[91m==> Removing '%s' from queue...\033[00m"
                  % (site, site))
    if len(sites) > 0:
        print("\n\033[96mGenerating feeds for:\033[00m\n")
        sites_to_gen(sites, site_dic)
        gen_feeds(sites, site_dic, backorder_site_list)
    else:
        input("\a\n😞 Nothing to do...hit 'Enter' to return to menu: \033[00m")


def gen_feeds(sites, site_dic, backorder_site_list):
    """Pass sites to feed generator"""
    input("Press 'Enter' to run the feed generator. 'CTRL+C' to quit...: ")
    print("\n\033[96mOkay, let me open some spreadsheets and...\033[00m")
    print("\n\033[92mGenerating feeds & sorting files...\033[00m\n")
    for site in sites:
        if site:
            if "multi_brand=True" in site_dic[site.lower()]:
                gen_multi_brand(qb_df, site, backorder_site_list,
                                brand_list, site_dic)
            else:
                merge_feed(qb_df, "%s" %
                           site, backorder_site_list, *site_dic[site.lower()])
        else:
            print('\aNo feeds to generate...\n\tValid sites:\n')
            print_sites(site_dic)
            sys.exit(1)
    input("\a\n\033[96m🍻 *clink* Done! Hit 'Enter' to return to menu: \033[00m")


def gen_all(site_dic, backorder_site_list):
    """Generate all feeds"""
    print("Generating feeds for all valid sites...\n")
    okay = input(
        "Press 'Enter' to run the feed generator. 'CTRL+C' to quit...: ")
    print("\n\033[96mOkay, let me open some spreadsheets and...\033[00m")
    print("\n\033[92mGenerating feeds & sorting files...\033[00m\n")
    for key in site_dic:
        if "multi_brand=True" in site_dic[key.lower()]:
            gen_multi_brand(qb_df, key, backorder_site_list,
                            brand_list, site_dic)
        else:
            merge_feed(qb_df, "%s" %
                       key, backorder_site_list, *site_dic[key.lower()])
    input("\a\n\033[96m🍻 *clink* Done! Hit 'Enter' to return to menu: \033[00m")


def gen_multi_brand(qb_df, site, backorder_site_list, brand_list, site_dic):
    """Generates separate brand feeds files for single site"""
    dir_is_full(len(brand_list), site)  # allow multiple files to reside
    for brand in brand_list:
        merge_feed(qb_df, site, backorder_site_list, *
                   site_dic[site.lower()], brand="%s" % brand)


def merge_feed(qb_df, site, backorder_site_list, join_key, new_qty, multi_brand=False, brand=False):
    """Creates and outputs csv files with updated inventory quantities from df.
    Negative qtys are replaced with 0.
    Generated feeds have index dropped and are exported and sorted if necessary.
    join_key col is reset to default after export is complete.
    """
    qb_df.rename(columns={'Item': join_key}, inplace=True)
    if multi_brand:
        site_df = pd.read_csv('data/inventory-templates/%s-%s.csv' %
                              (site, brand), sep=",", encoding="Latin-1", index_col=False)
    else:
        site_df = pd.read_csv('data/inventory-templates/%s.csv' %
                              site, sep=",", encoding="Latin-1", index_col=False)
    site_df[join_key] = site_df[join_key].astype(str)
    inv_feed = pd.merge(qb_df, site_df, on='%s' %
                        join_key, how='inner')  # inner join on key
    # move to qty col & remove qb col
    inv_feed[new_qty] = inv_feed['Quantity On Hand']
    del inv_feed['Quantity On Hand']
    inv_feed[new_qty] = inv_feed[new_qty].clip(lower=0)
    if site in rearrange_dic:  # swap cols if needed
        titles = list(inv_feed.columns)
        titles[rearrange_dic[site][0]], titles[rearrange_dic[site][1]
                                               ] = titles[rearrange_dic[site][1]], titles[rearrange_dic[site][0]]
        inv_feed = inv_feed[titles]
    if site in backorder_site_list:
        inv_feed = get_backorder_date(inv_feed, new_qty, site)
    if multi_brand:
        if not os.path.exists('data/generated-feeds/%s/newest' % site):
            os.makedirs('data/generated-feeds/%s/newest' % site)
        inv_feed.to_csv(r'data/generated-feeds/%s/newest/%s-feed-%s-%s-[%s].csv' % (
            site, site, brand, date, time), index=False)
        print(
            "\n✨ \033[1mSuccess!\033[0m \033[92mNew \033[1m%s - %s\033[0m csv file generated at:\033[00m" % (site.upper(), brand.upper()))
        print("\033[92m\033[96m\033[5m==>\033[0m\033[0m data/generated-feeds/%s/newest/%s-feed-%s-%s-[%s].csv\033[00m" %
              (site, site, brand, date, time))
    else:
        sort_feeds("%s" % site)
        if not os.path.exists('data/generated-feeds/%s/newest' % site):
            os.makedirs('data/generated-feeds/%s/newest' % site)
        inv_feed.to_csv(
            r'data/generated-feeds/%s/newest/%s-feed-%s-[%s].csv' % (site, site, date, time), index=False)
        print(
            "\n✨ \033[1mSuccess!\033[0m \033[92mNew \033[1m%s\033[0m csv file generated at:\033[00m" % site.upper())
        print("\033[92m\033[96m\033[5m==>\033[0m\033[0m data/generated-feeds/%s/newest/%s-feed-%s-[%s].csv\033[00m\n" %
              (site, site, date, time))
    qb_df.rename(columns={join_key: 'Item'}, inplace=True)


def get_backorder_date(inv_feed, new_qty, site):
    """Handle backorder/discontinued cols"""
    for col in inv_feed:  # find relevant cols in df
        if col in discontinued_cols:
            discontinued_col = col
        elif col in backorder_cols:
            backorder_col = col
    backorder_date = date.today() + relativedelta(months=+months_out)
    backorder_date = str(backorder_date)
    renew_backorder_date = date.today() - relativedelta(days=+days_before)
    renew_backorder_date = str(renew_backorder_date)
    if backorder_col:
        inv_feed[backorder_col].fillna('', inplace=True)
        inv_feed[backorder_col] = inv_feed[backorder_col].astype(
            str)  # sanitize NaN
        # check existing date if exists and update/skip
        if inv_feed.loc[inv_feed[backorder_col] > renew_backorder_date].empty:
            print('Generating new backorder date: %s' % backorder_date)
            inv_feed.loc[inv_feed[new_qty] != 0, [backorder_col]] = ''
            inv_feed.loc[inv_feed[new_qty] == 0,
                         [backorder_col]] = backorder_date
            if discontinued_col:
                inv_feed.loc[inv_feed[discontinued_col].notna(), [
                    backorder_col]] = ''
            print('Updating template...\n')
            if not os.path.exists('data/inventory-templates/old'):
                os.makedirs('data/inventory-templates/old')
            print('Moving old template to data/inventory-templates/old/...')
            move_old_template = 'mv data/inventory-templates/%s.csv data/inventory-templates/old/%s-old-%s%s.csv' % (
                site, site, date, time)
            os.system(move_old_template)
            inv_feed.to_csv(
                r'data/inventory-templates/%s.csv' % (site), index=False)
            print(
                '\n\033[92m\033[96m\033[5m==>\033[0m\033[0m Created updated template: data/inventory-templates/%s.csv\n' % site)

    return inv_feed


main_menu = {
    "g": [gen_feed_menu, lambda: gen_feed_menu(qb_path), "(g)enerate feeds"],
    "s": [send_email_menu, lambda: send_email_menu(), "(s)end feeds"]


}

email_menu = {
    "s": [send_by_site, lambda: send_by_site(receiver_info), "(s)end by site"],
    "f": [ftp_connect, lambda: ftp_connect(wayfair), "(f)tp upload"],
    "a": [send_all, lambda: send_all(), "(a)ll"]
}

gen_menu = {
    "s": [gen_by_site, lambda: gen_by_site(site_dic, backorder_site_list), "(s)ites"],
    "a": [gen_all, lambda: gen_all(site_dic, backorder_site_list), "(a)ll"]
}

# ---------------------------------------------------------------------
# The main event
# ---------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            os.system("less README.md")
            sys.exit(1)
    if qb_path.lower().endswith('.csv') == True and os.path.isfile(qb_path) == True:
        qb_path = qb_path
        qb_df = import_qb(qb_path)
        menu_loop(main_menu, qb_path)
    else:
        print(
            "\a\n\033[93m⚠️ Path to QB Inventory csv file (%s) is invalid.\nPlease set a valid path in `config/config.yml`\033[00m.\n" % qb_path)
