# -*- coding: utf-8 -*-
import datetime
from google.appengine.ext import webapp
from google.appengine.api import mail
from google.appengine.api import users

class TrialSendingmailHandler(webapp.RequestHandler):
	def get(self):
		mail_to = self.request.get('mail_to', '')
		# Validation.
		if mail_to is '' or not mail.is_email_valid(mail_to):
			self.response.set_status(400)
			self.response.headers['Content-type'] = 'text/plain'
			self.response.out.write("Invalid mail address.\n")
			self.response.out.write('mail_to: ' + mail_to)
			return

		user = users.get_current_user()
		if user:
			mail_from = user.email()
			send_test_mail(mail_from, mail_to)

			# Output.
			self.response.headers['Content-type'] = 'text/plain'
			self.response.out.write('Sent mail.')
		else:
			self.redirect(users.create_login_url(self.request.uri))

def send_test_mail(mail_from, mail_to):
	message = mail.EmailMessage()
	message.sender = mail_from
	message.to = mail_to
	now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	message.subject = "Test"
	message.body = "Date: %s" % now
	message.send()
