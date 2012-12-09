# -*- coding: utf-8 -*-
from google.appengine.ext import db

class ModelInput1(db.Model):
	value = db.StringProperty(verbose_name='value', multiline=True, required=True)

class ModelInput2(db.Model):
	value = db.StringProperty(verbose_name='value', multiline=True, required=True)

class ModelInput3(db.Model):
	value = db.StringProperty(verbose_name='value', multiline=True, required=True)

class TrialPocketAccount(db.Model):
	api_key = db.StringProperty(required=True)
	user_name = db.StringProperty(required=True)
	encrypted_password = db.StringProperty(required=True)
