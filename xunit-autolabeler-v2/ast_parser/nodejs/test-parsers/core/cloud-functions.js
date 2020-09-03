"use strict";

exports.parse = (
  testStatements,
  commandToDescribeMap,
  describeChain,
  testPaths
) => {
  // GCF Functions Framework tests (HTTP requests)
  // TODO this will NOT detect URLs that are part of template strings,
  //      or those specified as a "url" property
  //      (those will likely require recursion, or simply throw an error)`
  testStatements.forEach((statement) => {
    if (statement.type === "VariableDeclaration") {
      const httpInvocationExpr = statement.declarations[0].init;
      let httpFunctionUrls =
        httpInvocationExpr.argument &&
        httpInvocationExpr.argument.arguments &&
        httpInvocationExpr.argument.arguments[0];

      // Handle template strings and objects
      if (httpFunctionUrls && httpFunctionUrls.type === "TemplateLiteral") {
        httpFunctionUrls = httpFunctionUrls.quasis;
      }

      if (httpFunctionUrls && Array.isArray(httpFunctionUrls)) {
        httpFunctionUrls = httpFunctionUrls
          .filter((x) => x.value && x.value.raw !== "")
          .map((x) => x.value.raw || x.value)
          .map((x) => x.split("?")[0].replace(/(^\/)|(\/$)/g, ""));

        httpFunctionUrls.forEach((url) => {
          const key = url.toLowerCase;
          commandToDescribeMap[key] = commandToDescribeMap[key] || [];
          commandToDescribeMap[key].push({
            describeChain,
            testPaths,
          });
        });
      }
    }
  });
};
