"use strict";

module.exports = (testTokens) => {
  let filename;
  testTokens.body.forEach((x) => {
    if (x.declarations) {
      let filenameCandidates = x.declarations[0].init;
      if (!filenameCandidates) {
        return;
      }

      if (filenameCandidates.quasis) {
        // Template string
        filenameCandidates = filenameCandidates.quasis[0].value.raw;
      } else {
        // Standard string
        filenameCandidates = filenameCandidates.value;
      }

      if (typeof filenameCandidates === "string") {
        filename =
          filenameCandidates
            .split(/\/|\s/)
            .filter((x) => x.endsWith(".js"))[0] || filename;
      }
    }
  });

  return filename;
};
