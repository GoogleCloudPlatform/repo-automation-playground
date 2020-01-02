BASE_DIR="$(pwd)/$(dirname "$0")"

cd $BASE_DIR
bundle install --path vendor/bundle

## Basic test
cd $BASE_DIR/basic_test
bundle exec rspec --format RspecJunitFormatter --out all-tests.xml

## Coverage test
cd $BASE_DIR/coverage_test
bundle exec rspec --require ../coverage_helper.rb -e "test one"
