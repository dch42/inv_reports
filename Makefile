#---------------------------------------------------------------------
# Install deps & add exec permissions
#---------------------------------------------------------------------

init:
	pip3 install -r requirements.txt
	chmod +x ./inv_manager/inv_manager.py
	less README.md
	nano ./config/config.yml