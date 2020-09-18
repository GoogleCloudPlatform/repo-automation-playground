# Copyright 2020 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from flask import Flask
from werkzeug.routing import Rule


app = Flask(__name__)

# This is a valid Flask decorator, but it isn't used in
# our samples and is thus ignored by the flask_router parser
#
# This subpackage's tests depend on this behavior, and
# will need updating if support *is* added in the future.
#
# Relevant doc page:
#   https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
app.url_map.add(Rule('/unknown', endpoint='index'))


def route_no_decorator():
    return 'OK'


@app.endpoint('index')
def route_unknown_decorator():
    return 'OK'


@app.route()  # type: ignore
def route_no_args():
    return 'OK'


@app.route('/valid')
def valid_route():
    return 'OK'
