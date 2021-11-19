import yaml

with open('../config/config.yml', 'r') as stream:
    try:
        cfg = (yaml.safe_load(stream))
    except Exception as e:
        print(e)
