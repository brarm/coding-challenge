# coding-challenge
Take Home Challenge Solution

Install dependencies:
```bash
pip install --user -r requirements.txt
```

Run App
```bash
$: run_app.sh
```

### Endpoints
Method Endpoint \[Json Structure\]

```POST /customer/create  {'name':'', 'email':'', 'password':''}```

```DELETE /customer/delete  {'email':''}```

```GET /customer```

```POST /certificate/create {'email':''}```

```POST /certificate/activate {'email':''}```

```POST /certificate/deactivate {'email':'', 'key':''}```

```GET /certificate {'email':''}```


### Test App

Webhook [URL](https://enuddqm54vfmht7.m.pipedream.net)

Webhook [code](https://pipedream.com/@brargolf/certificate-webhook-p_3nCa7Dz)

```bash
# Create user
curl --request POST -H "Content-Type: application/json" --data '{"name":"name0", "email":"email0@site.com", "password":"password"}' http://127.0.0.1:5000/customer/create

# Create cert for user
curl --request POST -H "Content-Type: application/json" --data '{"email":"email0@site.com"}' http://127.0.0.1:5000/certificate/create

# Check certs for user
curl --request GET -H "Content-type: application/json" -H "Accept: application/json" --data '{"email":"email0@site.com"}' http://127.0.0.1:5000/certificate

# Deactivate cert
curl --request POST -H "Content-type: application/json" --data '{"email":"email0@site.com","key":"<private key>"}' http://127.0.0.1:5000/certificate/deactivate

# Activate cert
curl --request POST -H "Content-type: application/json" --data '{"email":"email0@site.com","key":"<private key>"}' http://127.0.0.1:5000/certificate/activate

# List all users
curl --request GET http://127.0.0.1:5000/customer

# Delete user
curl --request DELETE -H "Content-Type: application/json" --data '{"email":"email0@site.com"}' http://127.0.0.1:5000/customer/delete
```

### Assumptions and Tradeoffs
- sqlite3 was chosen for ease of integration with python, as well as low dependency requirements 
  - assuming single reader/writer for this scenario, as well as sufficient disk space for potential certificate scale
- users assumed to be differentiated by email address
  - sanity check thus simplified for all actions where an "identity" is required
- passwords are salted and hashed upon user creation, never stored as plaintext
  - however, since authentication is not required, subsequent requests to /customer/* only require email
  - certificate updates require email and private key of cert to modify
- certificates are given an auto-incrementing primary key
  - this could also be used as a record identifier when selecting cert to activate/deactivate
  - stuck with private key to stay closer to data structure requirements
