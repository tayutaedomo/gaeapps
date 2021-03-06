# -*- coding: utf-8 -*-
import os.path
from datetime import datetime, timedelta
import urllib
import Cookie
import cgi
import logging
import simplejson

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache

from fbweb.utils import use_session
from fbweb.utils import make_csrf_code
from fbweb.models import FacebookUser
from fbweb import settings

APP_ROOT = os.path.dirname(__file__)
SITE_URL_ROOT = 'http://iketrial.appspot.com/fbweb/'

class LoginPage(webapp.RequestHandler):
	@use_session(regenerate=False)
	def get(self):
		template_path = os.path.join(APP_ROOT, 'templates/login.tpl')
		self.response.headers['Content-type'] = 'text/html'
		self.response.out.write(template.render(template_path, {}))

class LogoutPage(webapp.RequestHandler):
	@use_session(regenerate=False)
	def get(self):
		session_id = self.request.cookies.get('coiled-session', None)
		# Clear memcach data.
		mc = memcache.Client()
		if session_id is not None:
			mc.delete(session_id, namespace='session')
		# Clear cookie data.
		expires_date = datetime.utcnow() - timedelta(days=1)
		expires_str = expires_date.strftime("%a, %d %b %Y %H:%M:%S UTC")
		cookie = Cookie.SimpleCookie()
		cookie['coiled-session'] = ''
		cookie["coiled-session"]["path"] = "/"
		cookie["coiled-session"]["expires"] = expires_str
		self.response.headers.add_header("Set-Cookie", cookie.output(header=''))
		self.redirect(SITE_URL_ROOT + 'login/')

class RedirectPage(webapp.RequestHandler):
	@use_session(regenerate=False)
	def get(self):
		redirect_uri = SITE_URL_ROOT + 'redirect/'
		if self.request.get('code', '') is '':
			# Connect to Facebook.
			self.session['state'] = make_csrf_code()
			params = {
				'client_id': settings.APP_ID,
				'redirect_uri': redirect_uri,
				'state': self.session['state'],
				'scope': 'user_website,friends_website',
			}
			url = 'https://www.facebook.com/dialog/oauth?' + urllib.urlencode(params)
			self.redirect(url)
		else:
			# Redirect from Facebook.
			if not self.session.has_key('state') or self.session['state'] != self.request.get('state'):
				logging.info('Invalid csrf.')
				return
			params = {
				'client_id': settings.APP_ID,
				'client_secret': settings.APP_SECRET,
				'code': self.request.get('code'),
				'redirect_uri': redirect_uri,
			}
			url = 'https://graph.facebook.com/oauth/access_token?' + urllib.urlencode(params)
			f = urllib.urlopen(url)

			# Get some info by Facebook API.
			parsed_contents = cgi.parse_qs(f.read())
			#logging.info(parsed_contents) # @@debug
			url = 'https://graph.facebook.com/me?access_token=' + parsed_contents['access_token'][0] + '&fields=name,picture'
			f = urllib.urlopen(url)
			me = simplejson.loads(f.read())

			# Save to Datastore.
			query = db.GqlQuery("SELECT * FROM FacebookUser WHERE facebook_user_id = '%s'" % (me['id']));
			query.fetch(1)
			#logging.info("User count: " + str(query.count())) # @@debug
			if (query.count(1) is 0):
				user = FacebookUser(
					facebook_user_id=me['id'],
					facebook_name=me['name'],
					facebook_picture=me['picture']['data']['url'],
					facebook_access_token=parsed_contents['access_token'][0])
				db.put(user)
				#logging.info('Created a user. ' + str(user)) # @@debug
			else:
				user = query.get()

			if (user is not None):
				# TODO: Need to regeneate session.
				self.session['user'] = user

			self.redirect(SITE_URL_ROOT + 'index/')

class IndexPage(webapp.RequestHandler):
	@use_session(regenerate=False)
	def get(self):
		if not self.session.has_key('user'):
			self.redirect(SITE_URL_ROOT + 'login/')
			return

		# Use other API.
		url = 'https://graph.facebook.com/me/friends?access_token=' + self.session['user'].facebook_access_token + '&fields=website'
		f = urllib.urlopen(url)
		parsed_contents = simplejson.loads(f.read())
		#logging.info(parsed_contents) # @@debug

		context = {'user': self.session['user']}
		template_path = os.path.join(APP_ROOT, 'templates/index.tpl')
		self.response.headers['Content-type'] = 'text/html'
		self.response.out.write(template.render(template_path, context))

class ClearSessionPage(webapp.RequestHandler):
	""" Development action. """
	def get(self):
		session_id = self.request.cookies.get('coiled-session', None)
		mc = memcache.Client()
		if session_id is None:
			return
		mc.delete(session_id, namespace='session')
		self.response.headers['Content-type'] = 'text/plain'
		self.response.out.write('Cleared.')


logging.getLogger().setLevel(logging.DEBUG)

application = webapp.WSGIApplication([
		(r'/fbweb/index/', IndexPage),
		(r'/fbweb/login/', LoginPage),
		(r'/fbweb/logout/', LogoutPage),
		(r'/fbweb/redirect/', RedirectPage),
		(r'/fbweb/session/clear/', ClearSessionPage),
])

def main():
	run_wsgi_app(application)

if __name__ == '__main__':
	main()
