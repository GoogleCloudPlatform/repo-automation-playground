IGNORED_METHOD_NAMES = [
    'run_command',
    'parse_command_line_args',
    'main'
]

REGION_TAG_GREP_ARGS = \
    f'grep -hr START .'.split(' ')
REGION_TAG_GREP_ARGS += ['--include=*.py', '--exclude=*/lib/*']
REGION_TAG_GREP_ARGS += ['--include=*.js', '--exclude=*/node_modules/*']
