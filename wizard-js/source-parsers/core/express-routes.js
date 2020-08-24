// Copyright 2020 Google LLC. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

'use strict';

const { EXPRESS_METHOD_NAMES } = require('../../constants')

exports.parse = (sourceTokens, sourcePath) => {
    const expressMethods = sourceTokens.body
        .filter(f => f.type === 'ExpressionStatement' && f.expression.callee)
        .map(f => f.expression)
        .filter(f => EXPRESS_METHOD_NAMES.includes(f.callee.property && f.callee.property.name))

    expressMethods.forEach(method => {
        method.drift = {
            httpMethod: method.callee.property.name,
            urlPath: method.arguments[0].value,
            sourcePath
        }
    });

    return expressMethods;
}
