require "rspec"

require_relative "../coverage"


describe "simple test" do
	it "test one" do
		expect(return_one).to eq(1)
	end

	it "test two" do
		expect(return_two).to eq(2)
	end
end