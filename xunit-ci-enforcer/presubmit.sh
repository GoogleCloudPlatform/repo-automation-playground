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

# This script operates on a single sample folder
# e.g. "functions/helloworld"

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

SAMPLE_TAGS=$(grep "\[START" *.* | cut -d':' -f2 | egrep -o '([a-z]|_)+' | sort | uniq)

if [[ $(pwd) == *"nodejs"* ]]; then
	echo -e 'Detected language: \e[92m\e[1mNode.js\e[0m'
	TEST_DESCRIBES=$(grep "describe(\\'" test/*.*)
	TEST_TAGS=$(clean_describe $TEST_DESCRIBES)
elif [[ $(pwd) == *"ruby"* ]]; then
	echo -e 'Detected language: \e[31m\e[1mRuby\e[0m'
	TEST_DESCRIBES=$(grep "describe " spec/*.*)
	TEST_TAGS=$(clean_describe $TEST_DESCRIBES)
elif [[ $(pwd) == *"php"* ]]; then
	echo -e 'Detected language: \e[36m\e[1mPHP\e[0m'
	TEST_METHOD_NAMES=$(grep "function test" test/quick*.* | rev | cut -d' ' -f1 | rev | cut -c 5-)
	TEST_METHOD_NAMES_SNAKE_CASE=$(snake_case $TEST_METHOD_NAMES)
	TEST_TAGS=$(clean_stop_words $TEST_METHOD_NAMES_SNAKE_CASE)
elif [[ $(pwd) == *"python"* ]]; then
	echo -e 'Detected language: \e[38;5;208m\e[1mPython\e[0m'
	TEST_CLASS_NAMES=$(grep "class " *_test.py | cut -d':' -f2 |  sed -E 's/^class (Test)*|\(\)$//g')
	TEST_CLASS_NAMES_SNAKE_CASE=$(snake_case $TEST_CLASS_NAMES)
	TEST_TAGS=$(clean_stop_words $TEST_CLASS_NAMES_SNAKE_CASE)
else
	echo '\e[31m\e[1mERROR\e[0m No supported language detected!'
fi

DIFF=$(diff <(echo "$SAMPLE_TAGS") <(echo "$TEST_TAGS") | grep '_' | sort)

DIFF_LABELED=$(echo "$DIFF" | sed "s/</Add tag to \\\033[91mTEST\\\033[0m:/g" | sed "s/>/Add tag to \\\033[36mSNIPPET\\\033[0m:/g" | sort)

if [[ -n $DIFF_LABELED ]]; then
	echo -e $DIFF_LABELED
	#exit 1
else
	echo "No mismatched region tags detected."
	#exit 0
fi
