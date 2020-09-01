import os
import sys

from python import invoker

if len(sys.argv) != 2:
    raise ValueError('Please specify exactly one [root] directory.')

root_dir = sys.argv[1]
output_file = os.path.join(root_dir, 'repo.json')

json_out = invoker.get_json_for_dir(root_dir)
with open(output_file, 'w') as f:
    f.write(json_out + '\n')

print(f'JSON written to: {output_file}')
print('Do not move this file!')
