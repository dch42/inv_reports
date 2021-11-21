# ---------------------------------------------------------------------
# Some helpers
# ---------------------------------------------------------------------
import glob
import os
from pathlib import Path


def cheers():
    input("\a\n\033[96m🍻 *clink* Done! Hit 'ENTER' to return to menu: \033[00m")


def nothing_to_do():
    input("\a\n😞 Nothing to do...hit 'Enter' to return to menu: \033[00m")


def make_dir_if_no(site, dir1, dir2=False):
    if dir2:
        if not os.path.exists(f'data/{dir1}/{site}/{dir2}'):
            os.makedirs(f'data/{dir1}/{site}/{dir2}')
    else:
        if not os.path.exists(f'data/{dir1}/{site}'):
            os.makedirs(f'data/{dir1}/{site}')


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


def validate_sites(dic):
    """Validate that user input exists in dic"""
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
    return sites


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
        sort_files(site, 'old', 'generated-feeds', '*', 'newest')


def sort_files(site, destination, dir1, item, dir2=False):
    make_dir_if_no(site, dir1, dir2)
    print(f"Moving files to {destination}...")
    file_sort = f"mv data/{dir1}/{site}/{dir2}/{item} data/{dir1}/{site}/{destination}/"
    os.system(file_sort)
