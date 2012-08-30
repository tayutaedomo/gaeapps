# -*- coding: utf-8 -*-
from google.appengine.ext import db

class FbnewsFacebookConnect(db.Model):
	#user_id = db.IntegerProperty(required=True, indexed=True)
	facebook_user_id = db.StringProperty(required=True, indexed=True)
	facebook_name = db.StringProperty(required=True)
	facebook_access_token = db.StringProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	modified = db.DateTimeProperty(auto_now=True)

