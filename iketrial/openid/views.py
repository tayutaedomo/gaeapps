# -*- coding: utf-8 -*-
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

# Reference: https://developers.google.com/appengine/articles/openid?hl=ja

openIdProviders = (
	'Google.com/accounts/o8/id', # shorter alternative: "Gmail.com"
	'Yahoo.com',
	'MySpace.com',
	'AOL.com',
	'MyOpenID.com',
	'yahoo.co.jp',
	# add more here
)

class MainHandler(webapp.RequestHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			# signed in already
			self.response.out.write('Hello <em>%s</em>! [<a href="%s">sign out</a>]' % (
				user.nickname(), users.create_logout_url(self.request.uri)))
		else:
			# let user choose authenticator
			self.response.out.write('Hello world! Sign in at: ')
			for p in openIdProviders:
				p_name = p.split('.')[0] # take "AOL" from "AOL.com"
				p_url = p.lower()		# "AOL.com" -> "aol.com"
				self.response.out.write('[<a href="%s">%s</a>]' % (
					users.create_login_url(federated_identity=p_url), p_name))

#logging.getLogger().setLevel(logging.DEBUG)

application = webapp.WSGIApplication([
	('/openid/', MainHandler),
], debug=True)

def main():
	run_wsgi_app(application)

if __name__ == '__main__':
	main()
