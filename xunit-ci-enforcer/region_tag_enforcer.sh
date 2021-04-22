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
	echo $1 | grep '_' | egrep -o '([a-z]|_)+' | grep '_' | sort -u
}

function check_dir {
	SAMPLE_TAGS="$(grep -h "\[START" *.* --exclude=\*.{yaml,yml,json,md} | egrep -o '([a-z]|_)+' | sort -u)"

	if [[ $(pwd) == *"nodejs"* ]]; then
		LANG_MESSAGE='Detected language: \x1b[92m\x1b[1mNode.js\x1b[0m'
		TEST_DESCRIBES=$(grep -h "describe(" *est/*.js)
		TEST_TAGS=$(clean_describe "$TEST_DESCRIBES")
	elif [[ $(pwd) == *"ruby"* ]]; then
		LANG_MESSAGE='Detected language: \x1b[31m\x1b[1mRuby\x1b[0m'
		TEST_DESCRIBES=$(grep -h "describe " spec/*.rb)
		TEST_TAGS=$(clean_describe "$TEST_DESCRIBES")
	elif [[ $(pwd) == *"php"* ]]; then
		LANG_MESSAGE='Detected language: \x1b[36m\x1b[1mPHP\x1b[0m'
		TEST_METHOD_NAMES=$(grep -h "function test" *est/*.php | rev | cut -d' ' -f1 | rev | cut -c 5-)
		TEST_METHOD_NAMES_SNAKE_CASE=$(snake_case "$TEST_METHOD_NAMES")
		TEST_TAGS=$(clean_stop_words "$TEST_METHOD_NAMES_SNAKE_CASE")
	elif [[ $(pwd) == *"python"* ]]; then
		LANG_MESSAGE='Detected language: \x1b[38;5;208m\x1b[1mPython\x1b[0m'
		TEST_CLASS_NAMES=$(grep -h "class " *_test.py | cut -d':' -f2 |  sed -E 's/^class (Test)*|\(\)$//g')
		TEST_CLASS_NAMES_SNAKE_CASE=$(snake_case "$TEST_CLASS_NAMES")
		TEST_TAGS=$(clean_stop_words "$TEST_CLASS_NAMES_SNAKE_CASE")
	else
		echo -e '\x1b[31m\x1b[1mERROR\x1b[0m No supported language detected!'
		true
		return # Do nothing
	fi

	# Allow listing
	#   Allow list one-character "tags" (e.g. "_") that are probably false positives
	SAMPLE_TAGS=$(echo "$SAMPLE_TAGS" | grep -E ".{2,}")
	TEST_TAGS=$(echo "$TEST_TAGS" | grep -E ".{2,}")

	#   Allow list tags containing "_setup"
	SAMPLE_TAGS=$(echo "$SAMPLE_TAGS" | grep -v "_setup")
	TEST_TAGS=$(echo "$TEST_TAGS" | grep -v "_setup")

	# Compute diffs

	DIFF="$(diff <(echo "$SAMPLE_TAGS") <(echo "$TEST_TAGS") | grep '_' | sort)"

	DIFF_LABELED=$(echo "$DIFF" | sed "s/</\\\nAdd tag to \\\x1b[91mTEST\\\x1b[0m:/g" | sed "s/>/\\\nAdd tag to \\\x1b[36mSNIPPET\\\x1b[0m:/g" | sort)

	if [[ -n $DIFF_LABELED ]]; then
		echo "--------------------------------------"
		echo -e "Checking directory: \x1b[1m$(pwd)\x1b[0m"
		echo -e "$LANG_MESSAGE"
		echo -e $DIFF_LABELED
		false
	else
		# No mismatched region tags detected
		true
	fi
}

STATUS=0
if [ "$#" -eq 0 ]; then
	check_dir "$(pwd)" || STATUS=1
else
	for DIR in "$@"
	do
		pushd "$DIR" > /dev/null
	    check_dir "$DIR" || STATUS=1
	    popd > /dev/null
	done
fi

# Fail if labels are missing
exit $STATUS
