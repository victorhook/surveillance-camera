import subprocess
import json

with open('credentials.json') as f:
    data = json.load(f)

img_settings = data['image']

remote_dir = '/mnt/plant_monitor/asd'

print(img_settings['remote_host'])
print(['ssh', img_settings['remote_host'], '"mkdir"',
                '"-p"', f'"{remote_dir}"'])
# Ensure that dir exists on remote machine
subprocess.run(['ssh', img_settings['remote_host'], '"mkdir"',
                '"-p"', f'"{remote_dir}"'])