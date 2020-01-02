// [START method_one]
// [START method_two]
const bar = () => {
	return 'I am a helper method!';
}
// [END method_one]
// [END method_two]


// [START method_one]
exports.methodOne = () => {
	bar();
	baz(null, null);

	return 1;
};
// [END method_one]

// [START method_two]
exports.methodTwo = () => {
	bar();
	baz(null, null);

	return 2;
}
// [END method_two]