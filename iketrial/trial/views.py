# -*- coding: utf-8 -*-
import os.path
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db


APP_ROOT = os.path.dirname(__file__)


class PythonpathPage(webapp.RequestHandler):
	def get(self):
		import sys
		context = {'path_list': sys.path}
		template_path = os.path.join(APP_ROOT, 'templates/pythonpath.html')
		self.response.headers['Content-type'] = 'text/html'
		self.response.out.write(template.render(template_path, context))

class EncodeTestPage(webapp.RequestHandler):
	def get(self):
		self.response.headers['Content-type'] = 'text/plain'
		self.response.out.write('%s\n' % ('あいうえお'))
		self.response.out.write('%s\n' % (u'あいうえお'))

class ModelInput1Page(webapp.RequestHandler):
	def get(self, value):
		logging.info('value -> ' + str(value))
		if value:
			# get parameters.
			import urllib
			value = urllib.unquote_plus(value)
			try:
				eid = int(self.request.get('eid', 0))
			except:
				eid = self.request.get('eid', '')
			key = str(self.request.get('key', ''))
			# logging parameters.
			logging.info('value unquoted -> ' + str(value))
			logging.info('eid -> ' + str(eid))
			logging.info('key -> ' + str(key))
			# create entities.
			from trial.models import ModelInput1
			kv_obj = db.Key.from_path('ModelInput1', value)
			e_get_v = ModelInput1.get(kv_obj)
			kk_obj = db.Key.from_path('ModelInput1', key)
			e_get_k = ModelInput1.get(kk_obj)
			if isinstance(eid, int):
				e_id = ModelInput1.get_by_id(eid)
			else:
				e_id = {}
			e_kname_k = ModelInput1.get_by_key_name(key)
			import hashlib
			md5 = hashlib.md5()
			md5.update(value)
			key_name = md5.hexdigest()
			e_kname_kn = ModelInput1.get_by_key_name(key_name)
#			e_gori = ModelInput1.get_or_insert(key_name, value=value)
			# create resoponse.
			self.response.headers['Content-type'] = 'text/html'
			template_path = os.path.join(APP_ROOT, 'templates/ModelInput1-2.html')
			self.response.out.write(template.render(template_path, {
				'value': value, 'key': key, 'eid': eid,
				'e_get_v': e_get_v, 'e_get_k': e_get_k, 'e_id': e_id,
				'e_kname_k': e_kname_k, 'e_kname_kn': e_kname_kn, #'e_gori': e_gori,
			}))
		else:
			from trial.models import ModelInput1
			entities = ModelInput1.all().fetch(10)
			template_path = os.path.join(APP_ROOT, 'templates/modelinput1.html')
			self.response.headers['Content-type'] = 'text/html'
			self.response.out.write(template.render(template_path, {'entities':entities}))
	
	def post(self, value):
		value = self.request.get('value', '')
		value = value.decode('utf-8')
		if value:
			from trial.models import ModelInput1
			key = db.Key.from_path('ModelInput1', value)
			entity = ModelInput1(key, value=value)
			entity.put()
		self.redirect('/trial/modelinput1/')

class ModelInput2Page(webapp.RequestHandler):
	def get(self, value):
		logging.info('value -> ' + str(value))
		if value:
			# get parameters.
			import urllib
			value = urllib.unquote_plus(value)
			eid = self.request.get('eid', '')
			key = str(self.request.get('key', ''))
			# logging parameters.
			logging.info('value unquoted -> ' + str(value))
			logging.info('eid -> ' + str(eid))
			logging.info('key -> ' + str(key))
			# create entities.
			from trial.models import ModelInput2
			e_kname = ModelInput2.get_by_key_name(eid)
			# create resoponse.
			self.response.headers['Content-type'] = 'text/html'
			template_path = os.path.join(APP_ROOT, 'templates/ModelInput2-2.html')
			self.response.out.write(template.render(template_path, {
				'value': value, 'key': key, 'eid': eid,
				'e_kname': e_kname,
			}))
		else:
			from trial.models import ModelInput2
			entities = db.GqlQuery("select * from ModelInput2").fetch(10)
			template_path = os.path.join(APP_ROOT, 'templates/modelinput2.html')
			self.response.headers['Content-type'] = 'text/html'
			self.response.out.write(template.render(template_path, {'entities':entities}))
	
	def post(self, value):
		value = self.request.get('value', '')
		value = value.decode('utf-8')
		if value:
			from trial.models import ModelInput2
			import hashlib
			md5 = hashlib.md5()
			md5.update(value)
			key_name = md5.hexdigest()
			entity = ModelInput2(key_name=key_name, value=value)
			entity.put()
		self.redirect('/trial/modelinput2/')

class ModelInput3Page(webapp.RequestHandler):
	def get(self, value):
		logging.info('value -> ' + str(value))
		if value:
			# get parameters.
			import urllib
			value = urllib.unquote_plus(value)
			eid = self.request.get('eid', '')
			key = str(self.request.get('key', ''))
			# logging parameters.
			logging.info('value unquoted -> ' + str(value))
			logging.info('eid -> ' + str(eid))
			logging.info('key -> ' + str(key))
			# create entities.
			from trial.models import ModelInput2
			e_kname = ModelInput2.get_by_key_name(eid)
			# create resoponse.
			self.response.headers['Content-type'] = 'text/html'
			template_path = os.path.join(APP_ROOT, 'templates/ModelInput3-2.html')
			self.response.out.write(template.render(template_path, {
				'value': value, 'key': key, 'eid': eid,
				'e_kname': e_kname,
			}))
		else:
			from trial.models import ModelInput3
			entities = ModelInput3.all().fetch(10)
			template_path = os.path.join(APP_ROOT, 'templates/modelinput3.html')
			self.response.headers['Content-type'] = 'text/html'
			self.response.out.write(template.render(template_path, {'entities':entities}))
	
	def post(self, value):
		value = self.request.get('value', '')
		value = value.decode('utf-8')
		if value:
			from trial.models import ModelInput3
			import hashlib
			md5 = hashlib.md5()
			md5.update(value)
			key_name = md5.hexdigest()
			key = db.Key.from_path('ModelInput3', value)
			entity = ModelInput3(key, key_name, value=value)
			entity.put()
		self.redirect('/trial/modelinput3/')


logging.getLogger().setLevel(logging.DEBUG)

application = webapp.WSGIApplication([
		(r'/trial/pythonpath/', PythonpathPage),
		(r'/trial/encodetest/', EncodeTestPage),
		(r'/trial/modelinput1/(.*?)/?', ModelInput1Page),
		(r'/trial/modelinput2/(.*?)/?', ModelInput2Page),
		(r'/trial/modelinput3/(.*?)/?', ModelInput3Page),
	])

def main():
	run_wsgi_app(application)

if __name__ == '__main__':
	main()
