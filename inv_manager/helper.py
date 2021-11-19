# ---------------------------------------------------------------------
# Some helper bois
# ---------------------------------------------------------------------
import glob
import os
from pathlib import Path


def sites_to_gen(sites, dic):
    """List sites to be passed to generator"""
    for site in sites:
        if site == 'all':
            for key in dic:
                if key != 'all':
                    print(f'\t {key}')
        else:
            print(f'\t {site}')
    print("\n")


def list_dir_ignore_hidden(path):
    """Returns files in (path) ignoring hidden .files"""
    return glob.glob(os.path.join(path, '*'))


def print_sites(dic):
    """Prints all valid site names from site_dic"""
    for key in dic:
        print(f"\t {key}")


def dir_is_full(max_feeds, site):
    """Allows multiple feeds to reside in newest before moving to old"""
    newest_folder = Path(f'data/generated-feeds/{site}/newest/')
    is_dir_full = list_dir_ignore_hidden(newest_folder)
    if len(is_dir_full) >= max_feeds:
        sort_feeds(site)


def sort_feeds(site):
    """Sorts generated (site) files for cleanliness and easier email automation"""
    if not os.path.exists(f'data/generated-feeds/{site}/old'):
        os.makedirs(f'data/generated-feeds/{site}/old')
    file_sort = f"mv -v data/generated-feeds/{site}/newest/* data/generated-feeds/{site}/old/"
    print("Moving unused files to 'old':")
    os.system(file_sort)
