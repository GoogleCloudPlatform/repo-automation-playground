if [[ "$VIRTUAL_ENV" == "" ]]
then
 	echo "ERROR: please:"
 	echo " - activate your virtualenv"
 	echo " - install pytest"
	exit 1
fi

BASE_DIR="$(pwd)/$(dirname "$0")"

## Basic test
cd $BASE_DIR/basic_test
pytest basic_test.py --junitxml=all-tests.xml --cov=. --cov-report xml

## Coverage test
cd $BASE_DIR/coverage_test
pytest --cov=. --cov-report xml -k "coverage_test and test_one"