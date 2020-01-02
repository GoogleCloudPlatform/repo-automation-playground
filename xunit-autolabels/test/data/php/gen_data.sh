BASE_DIR="$(pwd)/$(dirname "$0")"

cd $BASE_DIR
composer install

## Basic test
cd $BASE_DIR/basic_test
../vendor/bin/phpunit *.php --verbose --log-junit all-tests.xml

## Out of order test
cd $BASE_DIR/out_of_order_test
../vendor/bin/phpunit *.php --verbose --log-junit all-tests.xml

## Coverage test
cd $BASE_DIR/coverage_test
../vendor/bin/phpunit --coverage-clover coverage.xml coverageTest.php --filter testOne