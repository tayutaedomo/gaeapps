# -*- coding: utf-8 -*-
from google.appengine.ext import db

class ModelInput1(db.Model):
	value = db.StringProperty(verbose_name='値', multiline=True, required=True)

class ModelInput2(db.Model):
	value = db.StringProperty(verbose_name='値', multiline=True, required=True)

class ModelInput3(db.Model):
	value = db.StringProperty(verbose_name='値', multiline=True, required=True)
