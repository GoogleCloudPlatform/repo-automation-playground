import os
import constants
import subprocess


def __getFiles(root_dir, predicate):
    paths = [os.path.join(root_dir, p) for p in os.listdir(root_dir)
             if p != 'lib']
    folders = [p for p in paths if not os.path.isfile(p)]

    files = [p for p in paths if os.path.isfile(p)
             and predicate(os.path.basename(p))]

    for f in folders:
        files += __getFiles(f, predicate)

    return files


def get_python_files(root_dir):
    return __getFiles(root_dir, lambda p: p.endswith('.py'))


def get_yaml_files(root_dir):
    return __getFiles(root_dir, lambda p: p == '.drift-data.yml')


def get_region_tags(root_dir):
    proc = subprocess.Popen(
        constants.REGION_TAG_GREP_ARGS,
        stdout=subprocess.PIPE,
        cwd=root_dir)
    region_tags = proc.stdout.read().decode().split('\n')
    region_tags = [x.strip()[9:-1] for x in region_tags]
    region_tags = [x for x in region_tags if len(x) > 1]

    return list(set(region_tags))
