# inv-manager
Automates the creation and sending of inventory feed csv files for dropship portals, updating available quantity levels from a QuickBooks Desktop inventory report.

## Setup 🔧

### Installation

If you have git, clone the repo and change to directory:
~~~
git clone https://github.com/dch42/inv-manager.git && cd inv-manager
~~~

Running `make` will install dependencies and add executable permissions to relevant scripts.

~~~
make
~~~

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

(g)enerate feeds: Generate inventory feeds
(s)end feeds: Send inventory feeds
(q)uit/back

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
~~~

### Output 📂

The generated feeds are saved in the `data/generated-feeds` folder.

File sorting works like this:

- The most recently generated file resides in `data/generated-feeds/%brand/newest` (`mail_send` searches for this file)
- When a new feed is generated, any unsent files are moved to `data/generated-feeds/%brand/old`

Negative inventory levels are changed to `0`.

### Backorder & Discontinued Item Handling

For sites that require backorder dates in their feeds, the program will populate the field with a default date 3 months out from feed creation if the out of stock item is not discontinued. 

The date settings can be changed in `config.yml`.

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

### Attachments 📎

Attachments are taken from the ```data/generated-feeds/%brand/newest``` directory, and moved to ```data/generated-feeds/%brand/sent``` after being sent or uploaded as an attachment.

Sites requiring multiple feeds (one feed per brand) are specified in `config.yml`.

## Acknowledgements ✨

Makes use of the wonderful [🐼 library](https://github.com/pandas-dev/pandas)

