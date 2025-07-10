
## Setup
1. Clone the repo
2. Create virtualenv and activate it
3. Run `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and update variables
5. Run `python manage.py migrate`
6. Run `python manage.py runserver`


<!-- Backend integration update 1 -->

1. frameworK: Django, Django-restframework
2. Database: PostgreSQL
3. API: RESTful API
4. Authentication: JWT (JSON Web Token)
5. Testing: api testing


models created
1. user 
2. vendor / client 


Core API's
1.  /api/auth-signup 
2.  /api/auth-signin 
3.  /api/auth-signout


<!-- Frontend adjustment 1 -->
1. api.js services has been added to handle Backend api
2. login and signup functionality has been implemented
3. login and signup functionality has been tested
4. login formData should be updated to username & password, instead of email & password
5. let use izitoast or other libraries for alerts and notifications
