# -*- coding: utf-8 -*-
import os.path
from datetime import datetime, timedelta
import time
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

		news = get_newsfeed(self.session['user'].facebook_access_token)
		context = {
			'user': self.session['user'],
			'news': news,
		}
		template_path = os.path.join(APP_ROOT, 'templates/index.tpl')
		self.response.headers['Content-type'] = 'text/html'
		self.response.out.write(template.render(template_path, context))

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

		mc = memcache.Client()
		if session_id is not None:
			mc.delete(session_id, namespace='session')

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
				'scope': 'read_stream,',
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
			me = get_profile(parsed_contents['access_token'][0])

			# Save to Datastore.
			query = db.GqlQuery("SELECT * FROM FbnewsFacebookConnect WHERE facebook_user_id = '%s'" % (me['id']));
			if query.count(1) is 0:
				user = create_FbnewsFacebookConnect(me['id'], me['name'], parsed_contents['access_token'][0])
			else:
				user = query.get()

			if user is not None:
				self.session['user'] = user

			self.redirect('/fbnews/index/')

class AggregationHandler(webapp.RequestHandler):
	def get(self):
		now = datetime.utcnow()
		logging.info("Started to aggregate at %s" % (now)) # @@debug

		user = get_first_FacebookConnect()
		if user is None:
			# TODO: Send mail.
			logging.error('Can not get user info.')

		news = get_newsfeed(user.facebook_access_token)

		data = {}
		start_time, end_time = get_ten_minutes_times(now)
		for a_news in news['data']:
			a_name = a_news['from']['name']
			a_time = a_news['updated_time']

			fb_timestamp = get_utc_time_from_fb_datetime(a_time)
			if not is_now_ten_minutes(fb_timestamp, start_time, end_time):
				continue

			key = make_summary_key(start_time, a_name)
			if data.has_key(key):
				data[key] += 1
			else:
				data[key] = 1

		if not data:
			logging.info('Aggregation is empty')
		else:
			for key, count in data.iteritems():
				update_news_summary(key, count)
		return

class DirectStoringHandler(webapp.RequestHandler):
	""" Action for development. """
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

class ResetMemcachHandler(webapp.RequestHandler):
	""" Action for development. """
	@use_session(regenerate=True)
	def get(self):
		if not self.session.has_key('user'):
			user = get_first_FacebookConnect()
			if user is not None:
				me = get_profile(user.facebook_access_token)
				if me.has_key('id'):
					self.session['user'] = user
				else:
					user.delete()
			else:
				logging.info('FacebookConnect is empty.')
		self.redirect('/fbnews/index/')
		return

class ClearSessionHandler(webapp.RequestHandler):
	""" Action for development. """
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

	if parsed_contents == {} and f.getcode() != 200:
		return {'code':f.getcode()}

	return parsed_contents

def get_newsfeed(token):
	url = 'https://graph.facebook.com/me/home?access_token=' + token
	f = urllib.urlopen(url)
	parsed_contents = simplejson.loads(f.read())

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

def get_first_FacebookConnect():
	query = models.FbnewsFacebookConnect.all()
	if (query.count(1) is 0):
		logging.info('In get_first_FacebookConnect, FacebookConnect is empty.')
		return None
	else:
		return query.get()

def get_utc_time_from_fb_datetime(fb_datetime_str):
	 return float(datetime.strptime(fb_datetime_str, '%Y-%m-%dT%H:%M:%S+0000').strftime('%s'))

def utc_str_to_jst_datetime(utc_datetime_str):
	""" @@debug """
	jst_time = datetime.strptime(utc_datetime_str, '%Y-%m-%dT%H:%M:%S+0000')
	jst_time += timedelta(0, 3600*9)
	return jst_time

def get_ten_minutes_times(now):
	past = now - timedelta(0, 60*9+50)
	m = past.minute / 10 * 10
	start_time = time.mktime([past.year, past.month, past.day, past.hour, m, 0, 0, 0, 0])
	end_time = start_time + 60 * 10
	return start_time, end_time

def generate_hour_time(minute_timestamp):
	a_datetime = datetime.fromtimestamp(minute_timestamp)
	return datetime(a_datetime.year, a_datetime.month, a_datetime.day, a_datetime.hour, 0, 0)

def is_now_ten_minutes(a_time, start_time, end_time):
	return start_time <= a_time and a_time < end_time

def make_summary_key(timestamp, name):
	a_datetime = generate_hour_time(timestamp)
	a_timestamp = a_datetime.strftime('%s')
	return str(long(a_timestamp)) + '_' + name

def split_summary_key(key):
	elemtns = key.split('_')
	return float(elemtns[0]), elemtns[1]

def update_news_summary(key, count):
	time_priod, name = split_summary_key(key)
	summary = get_news_summary_by_key(key)
	if summary is None:
		a_datetime = datetime.fromtimestamp(time_priod)
		summary = models.FbnewsNewsSummary(summary_key=key, time_priod=a_datetime, name=name, count=count)
	else:
		summary.count += count
	summary.put()

def get_news_summary_by_key(key):
	query = db.GqlQuery("SELECT * FROM FbnewsNewsSummary WHERE summary_key = '%s'" % (key))
	return query.get()


logging.getLogger().setLevel(logging.DEBUG)

application = webapp.WSGIApplication([
		(r'/fbnews/index/',     IndexPageHandler),
		(r'/fbnews/login/',     LoginPageHandler),
		(r'/fbnews/logout/',    LogoutPageHandler),
		(r'/fbnews/redirect/',  RedirectHandler),
		(r'/fbnews/aggregate/', AggregationHandler),
		(r'/fbnews/develop/store/', DirectStoringHandler),
		(r'/fbnews/develop/reset/', ResetMemcachHandler),
		(r'/fbnews/develop/clear/', ClearSessionHandler),
])

def main():
	run_wsgi_app(application)

if __name__ == '__main__':
	main()
