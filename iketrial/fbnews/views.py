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

from fbnews.utils import use_session
from fbnews import utils
from fbnews import models
from fbnews import settings

APP_ROOT = os.path.dirname(__file__)
SITE_URL_ROOT = 'http://iketrial.appspot.com/fbnews/'

class IndexPageHandler(webapp.RequestHandler):
	@use_session(regenerate=False)
	def get(self):
		if not self.session.has_key('user'):
			self.redirect('/fbnews/login/')
			return

		try:
			news = get_newsfeed(self.session['user'].facebook_access_token)
			context = {
				'user': self.session['user'],
				'news': news,
			}
			template_path = os.path.join(APP_ROOT, 'templates/index.tpl')
			self.response.headers['Content-type'] = 'text/html'
			self.response.out.write(template.render(template_path, context))
		except Exception:
			# TODO: Catch exception.
			pass

class LoginPageHandler(webapp.RequestHandler):
	@use_session(regenerate=False)
	def get(self):
		template_path = os.path.join(APP_ROOT, 'templates/login.tpl')
		self.response.headers['Content-type'] = 'text/html'
		self.response.out.write(template.render(template_path, {}))

class LogoutPageHandler(webapp.RequestHandler):
	@use_session(regenerate=False)
	def get(self):
		session_id = self.request.cookies.get('coiled-session-fbnews', None)

		# Clear memcach data.
		mc = memcache.Client()
		if session_id is not None:
			mc.delete(session_id, namespace='session')

		# Clear cookie data.
		utils.remove_cookie_session(self.response.headers)
		self.redirect('/fbnews/login/')

class RedirectHandler(webapp.RequestHandler):
	@use_session(regenerate=False)
	def get(self):
		redirect_uri = SITE_URL_ROOT + 'redirect/'
		if self.request.get('code', '') is '':
			# Connect to Facebook.
			self.session['state'] = utils.make_csrf_code()
			params = {
				'client_id': settings.APP_ID,
				'redirect_uri': redirect_uri,
				'state': self.session['state'],
				'scope': 'read_stream',
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
			me = get_profile(parsed_contents['access_token'][0])

			# Save to Datastore.
			query = db.GqlQuery("SELECT * FROM FbnewsFacebookConnect WHERE facebook_user_id = '%s'" % (me['id']));
			if (query.count(1) is 0):
				create_FbnewsFacebookConnect(me['id'], me['name'], parsed_contents['access_token'][0])
			else:
				user = query.get()

			if (user is not None):
				# TODO: Need to regeneate session.
				self.session['user'] = user

			self.redirect('/fbnews/index/')

class DirectStoringHandler(webapp.RequestHandler):
	""" For Development action. """
	@use_session(regenerate=False)
	def get(self):
		token = self.request.get('token', '')

		me = get_profile(token)
		if me.has_key('code') and int(me['code']) != 200:
			self.response.set_status(400)
			self.response.headers['Content-type'] = 'text/plain'
			self.response.out.write("Failed to connect to Facebook.\n")
			self.response.out.write('Token: ' + token + "\n")
			self.response.out.write('Response: ' + str(me))

		user = create_FbnewsFacebookConnect(me['id'], me['name'], token)
		self.session['user'] = user

		self.response.headers['Content-type'] = 'text/plain'
		self.response.out.write("Succeeded to connect to Facebook.\n")

class ClearSessionHandler(webapp.RequestHandler):
	""" For Development action. """
	def get(self):
		session_id = self.request.cookies.get(utils.COOKIE_SESSION_KEY, None)
		if session_id is not None:
			mc = memcache.Client()
			mc.delete(session_id, namespace='session')
		utils.remove_cookie_session(self.response.headers)
		self.response.headers['Content-type'] = 'text/plain'
		self.response.out.write('Cleared.')

def get_profile(token):
	url = "https://graph.facebook.com/me?access_token=%s&fields=name" % (token)
	f = urllib.urlopen(url)
	parsed_contents = simplejson.loads(f.read())

	# Check response status.
	if parsed_contents == {} and f.getcode() != 200:
		return {'code':f.getcode()}

	return parsed_contents

def get_newsfeed(token):
	url = 'https://graph.facebook.com/me/home?access_token=' + token
	f = urllib.urlopen(url)
	parsed_contents = simplejson.loads(f.read())

	# Check response status.
	if parsed_contents == {} and f.getcode() != 200:
		return {'code':f.getcode()}

	return parsed_contents

def create_FbnewsFacebookConnect(user_id, name, token):
	user = models.FbnewsFacebookConnect(
		facebook_user_id=user_id,
		facebook_name=name,
		facebook_access_token=token)
	db.put(user)
	return user

def get_FacebookConnect_by_id(id):
	# TODO
	pass

def get_first_FacebookConnect(name):
	query = models.FbnewsFacebookConnect.all()
	if (query.count(1) is 0):
		logging.info('In get_first_FacebookConnect, FacebookConnect is empty.')
		return None
	else:
		return query.get()


logging.getLogger().setLevel(logging.DEBUG)

application = webapp.WSGIApplication([
		(r'/fbnews/index/',     IndexPageHandler),
		(r'/fbnews/login/',     LoginPageHandler),
		(r'/fbnews/logout/',    LogoutPageHandler),
		(r'/fbnews/redirect/',  RedirectHandler),
		(r'/fbnews/develop/store/', DirectStoringHandler),
		(r'/fbnews/develop/clear/', ClearSessionHandler),
])

def main():
	run_wsgi_app(application)

if __name__ == '__main__':
	main()
