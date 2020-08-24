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

exports.parse = (sourceTokens, sourcePath) => {
    let mainMethods = sourceTokens.body.map(x => x.declarations && x.declarations[0] || x);
    mainMethods = mainMethods.filter(f => f.id && f.id.name && f.id.name === 'main');

    mainMethods = mainMethods.map(f => {
        if (f.id.name === 'main') {  // HACK: some samples (e.g. nodejs-vision) wrap sample in a "main" method
            const subexpressions = (f.init || f).body.body.filter(x => x.id && x.id.name);
            if (subexpressions.length === 1) {
                return subexpressions[0];
            } else if (subexpressions.length > 1) {
                // main() methods should not have multiple subexpressions
                // (some files do though, and are handled by other parsers!)
                return null; 
            }
        }
        return f;
    }).filter(f => f);

    mainMethods.forEach(m => m.drift = {
        methodName: m.id.name,
        name: m.id.name,
        sourcePath
    });

    return mainMethods;
}
