#!/usr/bin/env python3

import sys
import argparse

class Customer:
	data = {'name':'', 'email': '', 'password':'', 'certificates':[]}

	def __init__(self):
		self.data=data={'name':'', 'email': '', 'password':'', 'certificates':[]}

	def __init__(self, name='', email='', password='', certificates=''):
		self.data['name'] = name,
		self.data['email'] = email,
		self.data['password'] = password,
		self.data['certificates'] = certificates

	def list_certs(self):
		for cert in self.certificates:
			print(cert.data['status'])
			print(cert.data['key'])
			print(cert.data['body'])
			print('--------------------')

class Certificate:
	data = {'status':'inactive','key':'', 'body': ''}

	def __init__(self):
		self.data = {'status':'inactive','key':'', 'body': ''}

	def __init__(self, status='inactive', key='', body=''):
		self.data['status'] = status
		self.data['key'] = key
		self.data['body'] = body

	def activate(self):
		if self.data['status'] == 'active':
			return
		elif self.data['status'] == 'inactive':
			self.data['status'] = 'active'
			# REST call to 
		else:
			self.data['status'] = 'inactive'

	def deactivate(self):
		if self.data['status'] == 'inactive':
			return
		elif self.data['status'] == 'active':
			self.data['status'] == 'inactive'
		else:
			self.data['status'] = 'inactive'

def certificate_manager(args):
	entity = args['entity']
	if entity == 'customer':
		name = ''
		email = ''
		password = ''
		if 'name' in args:
			name = args['name']
		else:
			name = input('Customer name: ')
		if 'email' in args:
			email = args['email']
		else:
			email = input('Customer email: ')
		if 'password' in args:
			password = args['password']
		else:
			password = input('Customer password: ')
	
	elif entity == 'certificate':
		pass


if __name__ == '__main__':
	parser = argparse.ArgumentParser(
			description='Manage users and their certificates',
			usage=' cman [customer, certificate]'\
					'\n\tcman customer --name <name> --email <email> --password <password>'
					'\n\tcman certificate --private-key <key> --cert-body <body>'
		)
	parser.add_argument('entity', choices=['customer', 'certificate'],
	                    help='The entity [Customer, Certificate]')
	parser.add_argument('--name', default=argparse.SUPPRESS,
						help='User name')
	parser.add_argument('--email', default=argparse.SUPPRESS,
						help='User email')
	parser.add_argument('--password', default=argparse.SUPPRESS,
						help='User password')
	parser.add_argument('--private-key', default=argparse.SUPPRESS,
						help='Certificate private key')
	parser.add_argument('--cert_body', default=argparse.SUPPRESS,
						help='Certificate body')

	args = parser.parse_args()
	certificate_manager(vars(args))
	sys.exit(0)
