import json
import yaml

with open('barrelstore_small.json') as json_file:
    data = json.load(json_file)

with open("test.yaml", 'w') as outfile:
		yaml.safe_dump(data, outfile, default_flow_style=False)
