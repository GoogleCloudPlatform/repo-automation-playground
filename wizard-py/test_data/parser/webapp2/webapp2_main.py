# Copyright 2015 Google Inc. All rights reserved.
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

##############################################################################
# NOTE: This file is mostly *sample data*, so it need not (necessarily) run! #
##############################################################################

# [START all]
import urllib
import webapp2


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("")


# [START image_handler]
class Image(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('No image')
# [END image_handler]


# [START sign_handler]
class Guestbook(webapp2.RequestHandler):
    def post(self):
        guestbook_name = self.request.get('guestbook_name')

        self.redirect('/?' + urllib.urlencode(
            {'guestbook_name': guestbook_name}))
# [END sign_handler]


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/img', Image),
                               ('/sign', Guestbook)],
                              debug=True)
# [END all]
