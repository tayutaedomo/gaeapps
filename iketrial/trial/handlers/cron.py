# -*- coding: utf-8 -*-
import logging

from google.appengine.ext import webapp

class TrialCronMinutesHandler(webapp.RequestHandler):
	def get(self):
		logging.info('Executed CronMinitues.')

		self.response.headers['Content-type'] = 'text/plain'
		self.response.out.write("OK")
