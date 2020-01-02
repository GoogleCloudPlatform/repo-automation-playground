// [START setup]
const app = {
	use: () => {},
	get: (cb) => {
		cb();
	}
};

app.use();
// [END setup]

// [START handle_request]
app.get((req, res) => {
	console.log('I am a fake Express middleware handler!')
})
// [END handle_request]