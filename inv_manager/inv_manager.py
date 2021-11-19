#!/usr/bin/env python3

import os
import sys
import time
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
import pyfiglet
from helper import cheers, sites_to_gen, print_sites, dir_is_full, sort_feeds
from mail_send import send_all, send_by_site, ftp_connect
from config import cfg

date = datetime.now().date()
time = datetime.now().time().strftime('%H-%M-%S')

dash = 70*'-'

PROG_VER = "1.1"

main_feed_path = (cfg['path_to_main_feed'])
feed_cols = (cfg['feed_cols'])


backorder_site_list = (cfg['backorder_site_list'])
backorder_cols = (cfg['backorder_cols'])
discontinued_cols = (cfg['discontinued_cols'])
months_out = (cfg['months'])
days_before = (cfg['days'])


site_dic = (cfg['site_dic'])
rearrange_dic = (cfg['rearrange_dic'])
multi_brand_dic = (cfg['multi_brand_dic'])


def menu_loop(menu):
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
        pyfiglet.print_figlet(f"{title}")
        print(f"Main inventory path: '{main_feed_path}'\n")
        print(f"Ver. {PROG_VER}")
        print("Pandas version: " + pd.__version__)
        print("Numpy version: " + np.__version__)
        print("\n\033[92mCreate and send updated inventory feed csv files to dropship portals.\n\n\tThe new feeds are saved in `data/generated-feeds`.\n\tThe templates are stored in `data/inventory-templates`.\033[00m\n")
        print(f"\n\033[1m#{dash}\n# Menu\n#{dash}\033[0m\n")
        for key, value in menu.items():
            print(
                f'\033[96m{value[2]}:\033[0m \033[95m{value[0].__doc__}\033[0m')
        print("\033[96m(q)uit/back\033[0m")
        print(f"\n\033[1m#{dash}\033[0m\n")
        choice = input('\nAction?: ').lower().strip()
        if choice in menu:
            menu[choice][1]()


def gen_feed_menu():
    """Generate inventory feeds"""
    menu_loop(gen_menu)


def send_email_menu():
    """Send inventory feeds"""
    menu_loop(email_menu)


def import_main_feed():
    """Import data from main csv"""
    df = pd.read_csv(main_feed_path, sep=",", encoding="Latin-1",
                     usecols=[feed_cols[0], feed_cols[1]])
    df[feed_cols[0]] = df[feed_cols[0]].astype(str)
    # df = df.replace({'(m-)': ''}, regex=True)  # sanitization zone
    print(f"\nMain Inventory Import Complete: {main_feed_path}\n")
    main_df = df
    return main_df


def gen_by_site():
    """Generate feeds for specific sites"""
    print("Valid sites:")
    print_sites(site_dic)
    sites = sites_raw = []
    sites_raw = input(
        "\nInput sites, seperated by space ('Enter' when done): ").split()
    for site in sites_raw:  # remove bogus input
        if site in site_dic:
            sites.append(site)
        else:
            print(
                f"\n\033[93m⚠️  Warning! No record of site '{site}'...\033[00m\n\033[91m==> Removing '{site}' from queue...\033[00m")
    if sites:
        print("\n\033[96mGenerating feeds for:\033[00m\n")
        sites_to_gen(sites, site_dic)
        gen_feeds(sites)
    else:
        input("\a\n😞 Nothing to do...hit 'Enter' to return to menu: \033[00m")


def gen_feeds(sites):
    """Pass sites to feed generator"""
    input("Press 'Enter' to run the feed generator. 'CTRL+C' to quit...: ")
    print("\n\033[96mOkay, let me open some spreadsheets and...\033[00m")
    print("\n\033[92mGenerating feeds & sorting files...\033[00m\n")
    for site in sites:
        if site:
            if site in multi_brand_dic.keys():
                gen_multi_brand(site)
            else:
                merge_feed(site, *site_dic[site.lower()])
        else:
            print('\aNo feeds to generate...\n\tValid sites:\n')
            print_sites(site_dic)
            sys.exit(1)
    cheers()


def gen_all():
    """Generate all feeds"""
    print("Generating feeds for all valid sites...\n")
    input("Press 'Enter' to run the feed generator. 'CTRL+C' to quit...: ")
    print("\n\033[96mOkay, let me open some spreadsheets and...\033[00m")
    print("\n\033[92mGenerating feeds & sorting files...\033[00m\n")
    for key in site_dic:
        if key in multi_brand_dic.keys():
            gen_multi_brand(key)
        else:
            merge_feed(key, *site_dic[key.lower()])
    cheers()


def gen_multi_brand(site):
    """Generates separate brand feeds files for single site"""
    dir_is_full(len(multi_brand_dic[site]),
                site)  # allow multiple files to reside
    for brand in multi_brand_dic[site]:
        merge_feed(site, *site_dic[site.lower()], brand=f"{brand}")


def merge_feed(site, join_key, new_qty, brand=False):
    """Creates and outputs csv files with updated inventory quantities from df.
    Negative qtys are replaced with 0.
    Generated feeds have index dropped and are exported and sorted if necessary.
    join_key col is reset to default after export is complete.
    """
    main_df.rename(columns={feed_cols[0]: join_key}, inplace=True)
    if site in multi_brand_dic.keys():
        site_df = pd.read_csv(
            f'data/inventory-templates/{site}-{brand}.csv', sep=",", encoding="Latin-1", index_col=False)
    else:
        site_df = pd.read_csv(
            f'data/inventory-templates/{site}.csv', sep=",", encoding="Latin-1", index_col=False)
    site_df[join_key] = site_df[join_key].astype(str)
    inv_feed = pd.merge(main_df, site_df, on=f'{join_key}', how='inner')
    # move to qty col & remove qb col
    inv_feed[new_qty] = inv_feed[feed_cols[1]]
    del inv_feed[feed_cols[1]]
    inv_feed[new_qty] = inv_feed[new_qty].clip(lower=0)
    if site in rearrange_dic:  # swap cols if needed
        titles = list(inv_feed.columns)
        titles[rearrange_dic[site][0]], titles[rearrange_dic[site][1]
                                               ] = titles[rearrange_dic[site][1]], titles[rearrange_dic[site][0]]
        inv_feed = inv_feed[titles]
    if site in backorder_site_list:
        inv_feed = get_backorder_date(inv_feed, new_qty, site)
    if site in multi_brand_dic.keys():
        if not os.path.exists(f'data/generated-feeds/{site}/newest'):
            os.makedirs(f'data/generated-feeds/{site}/newest')
        inv_feed.to_csv(
            fr'data/generated-feeds/{site}/newest/{site}-feed-{brand}-{date}-[{time}].csv', index=False)
        print(
            f"\n✨ \033[1mSuccess!\033[0m \033[92mNew \033[1m{site.upper()} - {brand.upper()}\033[0m csv file generated at:\033[00m")
        print(
            f'\033[92m\033[96m\033[5m==>\033[0m\033[0m data/generated-feeds/{site}/newest/{site}-feed-{brand}-{date}-[{time}].csv\033[00m\n')
    else:
        sort_feeds(site)
        if not os.path.exists(f'data/generated-feeds/{site}/newest'):
            os.makedirs(f'data/generated-feeds/{site}/newest')
        inv_feed.to_csv(
            fr'data/generated-feeds/{site}/newest/{site}-feed-{date}-[{time}].csv', index=False)
        print(
            f"\n✨ \033[1mSuccess!\033[0m \033[92mNew \033[1m{site.upper()}\033[0m csv file generated at:\033[00m")
        print(
            f'\033[92m\033[96m\033[5m==>\033[0m\033[0m data/generated-feeds/{site}/newest/{site}-feed-{date}-[{time}].csv\033[00m\n')
    main_df.rename(columns={join_key: feed_cols[0]}, inplace=True)


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
            print(f"Generating new backorder date: {backorder_date}")
            inv_feed.loc[inv_feed[new_qty] != 0, [backorder_col]] = ''
            inv_feed.loc[inv_feed[new_qty] == 0,
                         [backorder_col]] = backorder_date
            if discontinued_col:
                inv_feed.loc[inv_feed[discontinued_col].notna(), [
                    backorder_col]] = ''
            print("Updating template...\n")
            if not os.path.exists('data/inventory-templates/old'):
                os.makedirs('data/inventory-templates/old')
            print("Moving old template to data/inventory-templates/old/...")
            move_old_template = f'mv data/inventory-templates/{site}.csv data/inventory-templates/old/{site}-old-{date}{time}.csv'
            os.system(move_old_template)
            inv_feed.to_csv(
                fr'data/inventory-templates/{site}.csv', index=False)
            print(
                f'\n\033[92m\033[96m\033[5m==>\033[0m\033[0m Created updated template: data/inventory-templates/{site}.csv\n')

    return inv_feed


main_menu = {
    "g": [gen_feed_menu, lambda: gen_feed_menu(), "(g)enerate feeds"],
    "s": [send_email_menu, lambda: send_email_menu(), "(s)end feeds"]


}

email_menu = {
    "s": [send_by_site, lambda: send_by_site(), "(s)end by site"],
    "f": [ftp_connect, lambda: ftp_connect(), "(f)tp upload"],
    "a": [send_all, lambda: send_all(), "(a)ll"]
}

gen_menu = {
    "s": [gen_by_site, lambda: gen_by_site(), "(s)ites"],
    "a": [gen_all, lambda: gen_all(), "(a)ll"]
}

# ---------------------------------------------------------------------
# The main event
# ---------------------------------------------------------------------

if __name__ == '__main__':
    if main_feed_path.lower().endswith('.csv') is True and os.path.isfile(main_feed_path) is True:
        main_df = import_main_feed()
        menu_loop(main_menu)
    else:
        print(
            f"\a\n\033[93m⚠️ Path to main inventory csv file ({main_feed_path}) is invalid.\nPlease set a valid path in `config/config.yml`\033[00m.\n")
