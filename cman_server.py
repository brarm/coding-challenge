#!/usr/bin/env python3

import sqlite3
import warnings
import datetime
import requests
import hashlib
import uuid

from flask import Flask
from flask import request

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

REST_CLIENT = 'https://enuddqm54vfmht7.m.pipedream.net'

warnings.filterwarnings('ignore')
app = Flask(__name__)

instantiate_tables()

# Create customer and insert into db
# 	HTTP Method: POST
# 	Content Type: application/json
#	Fields: name, email, password
@app.route('/customer/create', methods=['POST'])
def customer_create():
	req_fields = ['name', 'email', 'password']
	content = request.json
	if not content or not check_for_req_fields(content, req_fields):
		return generate_err_message(req_fields)
	else:
		name = content['name']
		email = content['email']
		plaintext_pw = content['password']

	conn = sqlite3.connect('cman.db')
	curs = conn.cursor()
	
	# Hash password to store securely (non-plaintext)
	salt = uuid.uuid4().hex
	hashed_pw = hash_password(plaintext_pw, salt)
	customer = (name, email, hashed_pw, salt)

	insert_customer = 'INSERT INTO customer (name, email, password, salt) VALUES (?,?,?,?)'
	curs.execute(insert_customer, customer)

	id = curs.lastrowid
	close_db(conn)
	return f'User created. id: {id}', 200


# Delete customer from db
#	HTTP Method: Delete
#	Content Type: application/json
#	Fields: email
@app.route('/customer/delete', methods=['DELETE'])
def customer_delete():
	req_fields = ['email']
	content = request.json
	if not content or not check_for_req_fields(content, req_fields):
		return generate_err_message(req_fields)
	else:
		email = content['email']

	if not check_for_user(email):
		return f'User with email {email} not found', 400
	else:
		conn = sqlite3.connect('cman.db')
		curs = conn.cursor()

		delete_customer = 'DELETE from customer WHERE email=?'
		curs.execute(delete_customer, (email,))

		close_db(conn)
		return 'User deleted', 200


# List all customers
#	HTTP Method: GET
#	Returns: json containing all customers
@app.route('/customer', methods=['GET'])
def customer():
	conn = sqlite3.connect('cman.db')
	curs = conn.cursor()

	get_all = 'SELECT * from customer'
	curs.execute(get_all)
	customers = curs.fetchall()
	
	close_db(conn)
	return {'customers': customers}, 200


# Create certificate for given user
#	HTTP Method: POST
#	Content Type: application/json
#	Fields: email
@app.route('/certificate/create', methods=['POST'])
def certificate_create():
	req_fields = ['email']
	content = request.json
	if not content or not check_for_req_fields(content, req_fields):
		return generate_err_message(req_fields)
	else:
		email = content['email']

	if not check_for_user(email):
		return f'User with email {email} not found', 400
	else:
		key_and_cert = generate_self_signed_cert()
		query_fields = key_and_cert + (email,)

		conn = sqlite3.connect('cman.db')
		curs = conn.cursor()

		create_cert = 'INSERT INTO certificate (key, body, status, customer) VALUES (?, ?, "active", (SELECT DISTINCT email from customer WHERE email=?))'
		curs.execute(create_cert, query_fields)
		id = curs.lastrowid
		
		close_db(conn)
		return f'Certificate created. id: {id}', 200


# Deactivate a certificate
#	HTTP Method: POST
#	Content Type: application/json
#	Fields: email, key (certificate private key)
@app.route('/certificate/deactivate', methods=['POST'])
def certificate_deactivate():
	req_fields = ['email', 'key']
	content = request.json
	if not content or not check_for_req_fields(content, req_fields):
		return generate_err_message(req_fields)
	else:
		email = content['email']
		key = content['key']

	if not check_for_user(email):
		return f'User with email {email} not found', 400
	else:
		conn = sqlite3.connect('cman.db')
		curs = conn.cursor()
		
		deactivate_cert = 'UPDATE certificate SET status="inactive" WHERE key=?'
		curs.execute(deactivate_cert, (key,))
		id = curs.lastrowid

		# Make REST call to webhook
		payload = {'user': email, 'certificate': id, 'status': 'inactive', 'agent': 'cman'}
		r = requests.post(REST_CLIENT, data=payload)
		
		close_db(conn)
		return f'Certificate {id} deactivated.', 200


# Activate a certificate
#	HTTP Method: POST
# 	Content Type: application/json
#	Fields: email, key (certificate private key)
@app.route('/certificate/activate', methods=['POST'])
def certificate_activate():
	req_fields = ['email', 'key']
	content = request.json
	if not content or not check_for_req_fields(content, req_fields):
		return generate_err_message(req_fields)
	else:
		email = content['email']
		key = content['key']

	if not check_for_user(email):
		return f'User with email {email} not found', 400
	else:
		conn = sqlite3.connect('cman.db')
		curs = conn.cursor()
		
		activate_cert = 'UPDATE certificate SET status="active" WHERE key=?'
		curs.execute(activate_cert, (key,))
		id = curs.lastrowid

		# Make REST call to webhook
		payload = {'user': email, 'certificate': id, 'status': 'active', 'agent': 'cman'}
		r = requests.post(REST_CLIENT, data=payload)

		close_db(conn)
		return f'Certificate {id} activated.', 200


# Get all active certificates for a user
#	HTTP Method: GET
# 	Content Type: application/json
#	Returns: json containing all active certs
@app.route('/certificate', methods=['GET'])
def certificate_get():
	req_fields = ['email']
	content = request.json
	if not content or not check_for_req_fields(content, req_fields):
		return generate_err_message(req_fields)
	else:
		email = content['email']

	if not check_for_user(email):
		return f'User with email {email} not found', 400
	else:
		conn = sqlite3.connect('cman.db')
		curs = conn.cursor()
		
		get_all = 'SELECT * from certificate WHERE status="active" and customer=(SELECT DISTINCT email FROM customer WHERE email=?)'
		curs.execute(get_all, (email,))
		certificates = curs.fetchall()
		
		close_db(conn)
		return {'certificates': certificates}, 200	


# Helper method to instantiate sqlite tables
# Called directly after
def instantiate_tables():
	conn = sqlite3.connect('cman.db')
	curs = conn.cursor()

	customer_table = """
	CREATE TABLE IF NOT EXISTS customer (
		email text PRIMARY KEY,
		name text NOT NULL,
		password text NOT NULL,
		salt text NOT NULL)
	"""

	curs.execute(customer_table)

	certificate_table = """
	CREATE TABLE IF NOT EXISTS certificate (
		certid integer PRIMARY KEY,
		key text NOT NULL,
		body text NOT NULL,
		status text NOT NULL,
		customer text NOT NULL,
		FOREIGN KEY(customer) REFERENCES customer(email))
	"""

	curs.execute(certificate_table)
	conn.close()


# Hashing implemented to store password safely
# Since authentication not required, hashed value 
#	is not checked
def hash_password(password, salt):
	return hashlib.sha512(password.encode('utf-8') + salt.encode('utf-8')).hexdigest()


# Helper method to commit and close db connection
def close_db(conn):
	conn.commit()
	conn.close()


# Helper method to check for user existence
def check_for_user(email):
	conn = sqlite3.connect('cman.db')
	curs = conn.cursor()

	find_user = 'SELECT DISTINCT email from customer where email=?'
	curs.execute(find_user, (email,))
	if not curs.fetchone():
		close_db(conn)
		return False
	else:
		close_db(conn)
		return True


# Helper method to validate presence of fields
def check_for_req_fields(content, req_fields):
	for field in req_fields:
		if field not in content:
			return False
	return True


# Helper method to generate error string
#	Used in case some fields are missing
def generate_err_message(fields):
	string = "Missing required field"
	if len(fields) == 1:
		string = f'{string} ({field[0]})'
	else:
		string = f'{string}s ({",".join(fields)})'
	return string, 400


# Helper method to generate a self signed cert and private key
# Code from https://cryptography.io/en/latest/x509/tutorial.html#creating-a-self-signed-certificate
def generate_self_signed_cert():
	key = rsa.generate_private_key(
	    public_exponent=65537,
	    key_size=2048,
	)
	subject = issuer = x509.Name([
	    x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
	    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Texas"),
	    x509.NameAttribute(NameOID.LOCALITY_NAME, u"Austin"),
	    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"CloudFlare"),
	    x509.NameAttribute(NameOID.COMMON_NAME, u"cloudflare.com"),
	])
	cert = x509.CertificateBuilder().subject_name(
	    subject
	).issuer_name(
	    issuer
	).public_key(
	    key.public_key()
	).serial_number(
	    x509.random_serial_number()
	).not_valid_before(
	    datetime.datetime.utcnow()
	).not_valid_after(
	    # Our certificate will be valid for 10 days
	    datetime.datetime.utcnow() + datetime.timedelta(days=10)
	).add_extension(
	    x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
	    critical=False,
	# Sign our certificate with our private key
	).sign(key, hashes.SHA256())
	
	private_key = key.private_bytes(
						encoding=serialization.Encoding.PEM, 
						format=serialization.PrivateFormat.TraditionalOpenSSL, 
						encryption_algorithm=serialization.NoEncryption())
	certificate = cert.public_bytes(serialization.Encoding.PEM)

	return private_key.decode('utf-8'), certificate.decode('utf-8')

