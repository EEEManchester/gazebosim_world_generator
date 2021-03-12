import json
import yaml

json_file = 'barrelstore_small.json'
yaml_file = "test.yaml"


with open(json_file) as json_file:
    data = json.load(json_file)

with open(yaml_file, 'w') as outfile:
		yaml.safe_dump(data, outfile, default_flow_style=False)
