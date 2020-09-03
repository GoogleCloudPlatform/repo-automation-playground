"use strict";

exports.parse = (
  testStatements,
  commandToDescribeMap,
  describeChain,
  testPaths
) => {
  testStatements.forEach((statement) => {
    let entireCmd;

    if (statement.type === "VariableDeclaration") {
      let execStmt = statement.declarations[0].init;
      execStmt = execStmt.argument || execStmt;

      if (execStmt.callee && execStmt.callee.name === "execSync") {
        entireCmd = execStmt.arguments[0];
      }
    } else if (
      statement.expression &&
      statement.expression.type === "AssignmentExpression" &&
      statement.expression.right.arguments
    ) {
      entireCmd = statement.expression.right.arguments[0];
    }

    if (entireCmd) {
      entireCmd = entireCmd.quasis || [entireCmd];

      const [subCmd] = entireCmd
        .filter((c) => c.value)
        .map(
          (c) =>
            (c.value.raw === undefined ? c.value : c.value.raw)
              .replace("/", " ") // HACK: some snippets (e.g. nodejs-vision) use slashes in weird places
              .replace(/(^\s+|\s+$)/g, "")
              .replace(/(^node\s|\.js)/g, "") // for e.g. `node file.js` instead of `node file cmd``
              .split(" ")[0]
        )
        .filter((c) => c);

      if (!subCmd) {
        return;
      }

      // file paths are case-insensitive (at least on OS X)
      const key = subCmd.toLowerCase();
      commandToDescribeMap[key] = commandToDescribeMap[key] || [];
      commandToDescribeMap[key].push({
        describeChain,
        testPaths,
      });
    }
  });
};
