#!/bin/bash

# Copyright 2020 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------

# Possible invocations:
#   current directory:   ./region_tag_enforcer.sh
#   list of directories: ./region_tag_enforcer.sh <dir1> [<dir2> <dir3> ...]
# Args should be directories containing sample source code
# (not their parent directories or other "ancestors"!)

function snake_case {
	echo "$1" | sed -E 's/([A-Z])/_\1/g' | awk '{print tolower($0)}' | sed -E 's/^_//g'
}

function clean_stop_words {
	# Should/Does
	SHOULD_DOES=$(echo $1 | sed -E "s/_should_.*|_does_.*//g")
	
	# Plus
	STOP_WORDS=$(echo $SHOULD_DOES | sed 's/_plus_/\'$'\n/g')

	# Parenthesis + cleanup
	echo $STOP_WORDS | sed -E 's/\(\)$//g' | grep '_' | sort | uniq
}

function clean_describe {
	echo $1 | cut -d':' -f2 | grep '_' | egrep -o '([a-z]|_)+' | grep '_' | sort | uniq
}

function check_dir {
	echo -e "Checking directory: \x1b[1m$(pwd)\x1b[0m"

	SAMPLE_TAGS=$(grep "\[START" *.* | cut -d':' -f2 | egrep -o '([a-z]|_)+' | sort | uniq)

	if [[ $(pwd) == *"nodejs"* ]]; then
		echo -e 'Detected language: \x1b[92m\x1b[1mNode.js\x1b[0m'
		TEST_DESCRIBES=$(grep "describe(\\'" test/*.*)
		TEST_TAGS=$(clean_describe $TEST_DESCRIBES)
	elif [[ $(pwd) == *"ruby"* ]]; then
		echo -e 'Detected language: \x1b[31m\x1b[1mRuby\x1b[0m'
		TEST_DESCRIBES=$(grep "describe " spec/*.*)
		TEST_TAGS=$(clean_describe $TEST_DESCRIBES)
	elif [[ $(pwd) == *"php"* ]]; then
		echo -e 'Detected language: \x1b[36m\x1b[1mPHP\x1b[0m'
		TEST_METHOD_NAMES=$(grep "function test" test/quick*.* | rev | cut -d' ' -f1 | rev | cut -c 5-)
		TEST_METHOD_NAMES_SNAKE_CASE=$(snake_case $TEST_METHOD_NAMES)
		TEST_TAGS=$(clean_stop_words $TEST_METHOD_NAMES_SNAKE_CASE)
	elif [[ $(pwd) == *"python"* ]]; then
		echo -e 'Detected language: \x1b[38;5;208m\x1b[1mPython\x1b[0m'
		TEST_CLASS_NAMES=$(grep "class " *_test.py | cut -d':' -f2 |  sed -E 's/^class (Test)*|\(\)$//g')
		TEST_CLASS_NAMES_SNAKE_CASE=$(snake_case $TEST_CLASS_NAMES)
		TEST_TAGS=$(clean_stop_words $TEST_CLASS_NAMES_SNAKE_CASE)
	else
		echo -e '\x1b[31m\x1b[1mERROR\x1b[0m No supported language detected!'
	fi

	DIFF=$(diff <(echo "$SAMPLE_TAGS") <(echo "$TEST_TAGS") | grep '_' | sort)

	DIFF_LABELED=$(echo "$DIFF" | sed "s/</\\\nAdd tag to \\\x1b[91mTEST\\\x1b[0m:/g" | sed "s/>/\\\nAdd tag to \\\x1b[36mSNIPPET\\\x1b[0m:/g" | sort)

	if [[ -n $DIFF_LABELED ]]; then
		echo -e $DIFF_LABELED
	else
		echo "No mismatched region tags detected."
	fi
}

if [ "$#" -eq 0 ]; then
	check_dir "$(pwd)"
else
	for DIR in "$@"
	do
		pushd "$DIR"
	    check_dir "$DIR"
	    popd
	    echo "--------------------------------------"
	done
fi
