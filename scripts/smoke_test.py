from django.test import Client
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

c = Client()

print('Anonymous: GET /')
r = c.get('/')
print(r.status_code)

print('Anonymous: GET /en/appointments/')
r = c.get('/en/appointments/')
print(r.status_code)

# Try to login with first superuser if exists
try:
    user = User.objects.filter(is_superuser=True).first()
    if user:
        print('Logging in as superuser', user.username)
        c.force_login(user)
        r = c.get('/en/appointments/')
        print('Authenticated appointments status:', r.status_code)
    else:
        print('No superuser found; skipping authenticated checks')
except Exception as e:
    print('Error during authenticated checks:', e)
