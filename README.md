# inv-manager
Automates the creation and sending of inventory feed csv files for dropship portals, updating available quantity levels from a central inventory report. 

Tested using inventory report from QuickBooks Desktop.

## Setup 🔧

### Installation

Clone the repo and change to directory:
~~~
git clone https://github.com/dch42/inv-manager.git && cd inv-manager
~~~

Running `make` will install dependencies and add executable permissions to relevant scripts.

~~~
make
~~~

Running `make` will also open this README.md with less, followed by opening `config.yml` in nano (feel free to exit and populate in an editor of your choice). 

### Config

Fill out the configuration file at `config/config.yml`.

(More detailed instructions can be found in the file itself.)

### CSV Templates

For each site, place a copy of an inventory feed csv file in `data/inventory-templates`.

Templates must be named to match the associated site (e.g. the template for 'dropshipsite' should be titled `dropshipsite.csv`, case insensitive). 

SKUs in template files can be changed/updated, and the generated files will update accordingly so long as SKUs are present in the QuickBooks csv. 

## Usage
Run the program (assuming cwd is ./inv-manager):

~~~
./inv_manager.py
~~~

You will be greeted with a menu:

~~~
 ___                 __  __                                   
|_ _|_ ____   __    |  \/  | __ _ _ __   __ _  __ _  ___ _ __ 
 | || '_ \ \ / /____| |\/| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|
 | || | | \ V /_____| |  | | (_| | | | | (_| | (_| |  __/ |   
|___|_| |_|\_/      |_|  |_|\__,_|_| |_|\__,_|\__, |\___|_|   
                                              |___/           

Main inventory path: './data/qb_feed.csv'
Logged in as youraddress@example.com to smtp.example.com on port 465...

Ver. 1.1
Pandas version: 1.3.4
Numpy version: 1.21.4

Create and send updated inventory feed csv files to dropship portals.

	The new feeds are saved in `data/generated-feeds`.
	The templates are stored in `data/inventory-templates`.

#---------------------------------------------------------------------
# Menu
# --------------------------------------------------------------------

(g)enerate feeds: Generate inventory feeds
(s)end feeds: Send inventory feeds
(q)uit/back

#---------------------------------------------------------------------

Action?: 
~~~

Type your selection (`g/s/q`) followed by `Enter`.

This menu/action structure is used throughout the program.

## Feed Generation 📋

Selecting `g` summons the following menu:

~~~
(s)ites: Generate feeds for specific sites
(a)ll: Generate all feeds
(q)uit/back
~~~

Selecting `a` will generate feeds for all sites specified in `config.yml`.

Selecting `s` will prompt you to select sites from a list:
~~~
Valid sites:
	 site1
	 site2
	 site3
	 site4
	 site5

Input sites, seperated by space ('Enter' when done): 
~~~

Typing `site1 site3 site5` will generate feeds for those sites, ignoring the rest.

Invalid sites are removed from the queue. `site1 site2 typo` will yield:

~~~
⚠️  Warning! No record of site 'typo'...
==> Removing 'typo' from queue...

Generating feeds for:

	 site1
	 site2

Press 'Enter' to run the feed generator. 'CTRL+C' to quit...: 
~~~

### Output 📂

~~~
Generating feeds & sorting files...

Moving unused files to 'old':
data/generated-feeds/site1/newest/site1-feed-2021-11-14-[23-09-15].csv -> data/generated-feeds/site1/old/site1-feed-2021-11-14-[23-09-15].csv

✨ Success! New SITE1 csv file generated at:
==> data/generated-feeds/site1/newest/site1-feed-2021-11-14-[23-36-44].csv

Moving unused files to 'old':
data/generated-feeds/site2/newest/site2-feed-2021-11-14-[23-09-15].csv -> data/generated-feeds/site2/old/site2-feed-2021-11-14-[23-09-15].csv

✨ Success! New SITE2 csv file generated at:
==> data/generated-feeds/site2/newest/site2-feed-2021-11-14-[23-36-44].csv

🍻 *clink* Done! Hit 'Enter' to return to menu: 
~~~

Negative inventory levels are changed to `0`.

The generated feeds are saved in the `data/generated-feeds` folder.

If directories don't exist, the program will create them.

- The most recently generated file resides in `data/generated-feeds/%brand/newest` (`mail_send` searches for this file)
- When a new feed is generated, any unsent files are moved to `data/generated-feeds/%brand/old`
- When a file is sent or uploaded as an attachment, it is moved to `data/generated-feeds/%brand/sent`

Directory hierarchy will look like this:
~~~
generated-feeds/
├── site
│   ├── newest
│   ├── old
│   └── sent
├── site1
│   ├── newest
│   ├── old
│   └── sent
├── site2
│   ├── newest
│   ├── old
│   └── sent
~~~

### Backorder & Discontinued Item Handling

Backorder settings can be tailored in `config.yml`.

For sites that require backorder dates in their feeds: 
- The program will populate the field with a date `x` months out from feed creation if the out of stock item is not marked discontinued.
- The program will update the inventory template accordingly, moving the old template to `data/inventory-templates/old`.
- Once backorder dates are set, they will not be overwritten unless the item is still out of stock `y` days before generation. 

Marking items as discontinued should be done manually to the inventory template csv file beforehand.

## Sending Feeds ✉️

Selecting `s` at the main menu will summon:

~~~
(s)end by site: Send inventory emails to select sites
(f)tp upload: Upload inventory files via FTP
(a)ll: Send inventory emails to all sites
(q)uit/back
~~~

Selecting `a` will send inventory emails to all valid sites present in `config.yml`.

Selecting `f` will attempt to connect to an ftp server and upload the relevant file to specified upload directory.

Selecting `s` will prompt you with a list of sites to send inventory emails to.

All options will show a preview of the attachment and email generated, prompting for confirmation before sending or uploading.

~~~
########################################################################
# Email #1/1 (SITE)
# ---------------------------------------------------------------------

ATTACHMENT:
site-feed-2021-11-14-[23-09-15].csv 
(data/generated-feeds/site/newest/site-feed-2021-11-14-[23-09-15].csv)
SEND TO:
Site (receiver_address@email.com)
SUBJECT:
2021-11-14 Company Inventory Feed for Site
BODY:
Content-Type: text/plain; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit

Hi Name,

Attached is an updated inventory feed of our products.

Best Regards,
Company

#---------------------------------------------------------------------
# End of email
###################################################################### 

Do you want to send this email? (y/N): 
~~~

### Attachments 📎

Only .csv files are accepted as attachments, ignoring any pesky .hidden_files.

Attachments are taken from the ```data/generated-feeds/%brand/newest``` directory, and moved to ```data/generated-feeds/%brand/sent``` after being sent or uploaded as an attachment.

Sites requiring multiple feeds (one feed per brand) are specified in `config.yml`.

## Acknowledgements ✨

Makes use of the wonderful [🐼 library](https://github.com/pandas-dev/pandas)

