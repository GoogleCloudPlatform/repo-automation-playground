"use strict";

module.exports = (testTokens) => {
  let topLevelRegionTags = testTokens.body
    .filter((s) => s.type === "VariableDeclaration")
    .map((s) => s.declarations[0].init)
    .filter((i) => i && i.type.endsWith("Literal"));

  topLevelRegionTags = topLevelRegionTags.map((x) =>
    x.quasis ? x.quasis[0].value.raw : x.value
  );
  return topLevelRegionTags;
};
