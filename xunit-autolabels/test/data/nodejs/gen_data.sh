BASE_DIR="$(pwd)/$(dirname "$0")"
cd $BASE_DIR

npm install

## Basic test
cd $BASE_DIR/basic_test
mocha  --reporter xunit --exit --reporter-option="output=all-tests.xml" *.test.js

## Hook test
cd $BASE_DIR/hook_test
mocha  --reporter xunit --exit --reporter-option="output=all-tests.xml" *.test.js

## Overlapping filters test
cd $BASE_DIR/filter_overlap_test
mocha  --reporter xunit --exit --reporter-option="output=all-tests.xml" *.test.js

## Coverage test
cd $BASE_DIR/coverage_test
nyc --all --reporter=clover --report-dir="coverage_test/test-test-one" mocha *.test.js --grep "test one" --exit
nyc --all --reporter=clover --report-dir="coverage_test/test-test-two" mocha *.test.js --grep "test two" --exit

## Tabs/spaces test
cd $BASE_DIR/tabs_spaces_test
nyc --all --reporter=clover --report-dir="tabs_spaces_test/test-test-tabs" mocha *.test.js --grep "test tabs" --exit
nyc --all --reporter=clover --report-dir="tabs_spaces_test/test-test-spaces" mocha *.test.js --grep "test spaces" --exit
nyc --all --reporter=clover --report-dir="tabs_spaces_test/all" mocha *.test.js --exit

## Denylisted filenames test
cd $BASE_DIR/filename_denylist_test
nyc --all --reporter=clover --report-dir="filename_denylist_test" mocha *.test.js --exit

## Region tag test
cd $BASE_DIR/region_tags_test
nyc --all --reporter=clover --report-dir="region_tags_test" mocha *.test.js --exit
mocha  --reporter xunit --exit --reporter-option="output=all-tests.xml" *.test.js

## Per-dir main test
cd $BASE_DIR/per_dir_main_test
mocha  --reporter xunit --exit --reporter-option="output=all-tests.xml" test/*.test.js
nyc --all --reporter=clover --report-dir="per_dir_main_test/test-return_one" mocha test/*.test.js --grep "return_one" --exit
nyc --all --reporter=clover --report-dir="per_dir_main_test/test-return_two" mocha test/*.test.js --grep "return_two" --exit
