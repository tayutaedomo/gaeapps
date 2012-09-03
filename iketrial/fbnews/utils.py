# -*- coding: utf-8 -*-
import os
import pickle
import hashlib
import Cookie
import uuid
import random 
from datetime import datetime, timedelta

from google.appengine.ext.webapp import template, util
from google.appengine.api import memcache

COOKIE_SESSION_KEY = 'coiled-session-fbnews'

def use_session(regenerate):
	""" Refer from http://d.hatena.ne.jp/coiledcoil/20110212/1297491800 . """
	def use_session_internal(func):
		def use_session_decorator(self):
			self.session_id = None
			self.session = None

			session_id = self.request.cookies.get(COOKIE_SESSION_KEY, None)
			mc = memcache.Client()
			if session_id is not None:
				session = mc.get(session_id, 'session')
				if session is not None:
					self.session = session
					if regenerate:
						mc.delete(session_id, namespace="session")
						self.session_id = hashlib.sha1(str(uuid.uuid4())).hexdigest()
					else:
						self.session_id = session_id

			if self.session_id is None:
				self.session_id = hashlib.sha1(str(uuid.uuid4())).hexdigest()
				self.session = {}

			set_cookie_session(self.response.headers, self.session_id)

			func(self)

			if self.session_id is not None:
				if self.session is None:
					mc.delete(self.session_id, namespace="session")
				else:
					mc.set(self.session_id, self.session, time=60*60*24, namespace="session")
		return use_session_decorator

	return use_session_internal

def set_cookie_session(headers, session_id):
	expires_date = datetime.utcnow() + timedelta(days=1)
	# expires_str = expires_date.strftime("%d %b %Y %H:%M:%S GMT")
	expires_str = expires_date.strftime("%a, %d %b %Y %H:%M:%S UTC")
	cookie = Cookie.SimpleCookie()
	cookie[COOKIE_SESSION_KEY] = session_id
	cookie[COOKIE_SESSION_KEY]["path"] = "/"
	cookie[COOKIE_SESSION_KEY]["expires"] = expires_str
	headers.add_header("Set-Cookie", cookie.output(header=''))

	return headers

def remove_cookie_session(headers):
	expires_date = datetime.utcnow() - timedelta(days=1)
	expires_str = expires_date.strftime("%a, %d %b %Y %H:%M:%S UTC")
	cookie = Cookie.SimpleCookie()
	cookie[COOKIE_SESSION_KEY] = ''
	cookie[COOKIE_SESSION_KEY]["path"] = "/"
	cookie[COOKIE_SESSION_KEY]["expires"] = expires_str
	self.response.headers.add_header("Set-Cookie", cookie.output(header=''))

def make_random_str(num):
	s = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz123456789[]{}!$%&'()-^¥:;*+><"
	string = ""
	for i in range(num):
		x = random.randint(0,len(s)-1)
		string += s[x]
	return string

def	make_csrf_code():
	return hashlib.sha1(make_random_str(16)).hexdigest()
