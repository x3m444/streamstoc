# Cum Adauga Un Nou Utilizator in Stoc App

## Metoda 1: Django Admin (Easiest) ✅

### Steps:

1. **Accesează Django Admin**
   ```
   https://stoc.kduner.duckdns.org/admin/
   ```
   (Login cu superuser — creator baza de date)

2. **Navigă la Users → Add User**
   - Click "Utilizatori" → "+ Add Utilizator"
   - Introdu:
     - Username: `costel` (exemplu)
     - Password: (Django auto-generates secure password)
     - Confirm password: (repeat)
   - Click "Save and continue editing"

3. **Set Permissions**
   - Check "Staff status" (dacă vrei sa poate merge la admin)
   - Check "Active" (user activ)
   - **Permisiuni Stoc**:
     - Leave "Read-only" unchecked → Full access (edit data)
     - Check "Read-only" → Doar rapoarte, no data entry

4. **Set Preferințe (Navă, Tractator)**
   - Navigă la "Preferințe utilizator"
   - Click "+ Add Preferințe utilizator"
   - Select user: Costel
   - Navă implicită: 978 (exemplu)
   - Tractator implicit: COSTEL (exemplu)
   - Click "Save"

5. **User e creat!**
   - Login cu username `costel` și password-ul

---

## Metoda 2: Command Line (Django Shell)

```bash
# Pe K3s
kubectl exec -it deployment/django-stoc -n default -- bash

# În container
python manage.py shell
```

```python
from apps.stoc.models import StocUser, UserPreferences

# Create user
user = StocUser.objects.create_user(
    username='ion',
    email='ion@example.com',
    password='SecurePassword123!',
    first_name='Ion',
    last_name='Popescu',
    is_readonly=False,  # False = full access, True = read-only
    is_active=True,
)

# Create preferences
prefs = UserPreferences.objects.create(
    user=user,
    default_nava=978,
    default_tragator='ION'
)

print(f"User created: {user.username}")
print(f"Preferences: Nava={prefs.default_nava}, Tractator={prefs.default_tragator}")
```

---

## Metoda 3: Django Migrations + Fixtures (Production)

Create fixture file — `apps/stoc/fixtures/initial_users.json`:

```json
[
  {
    "model": "stoc.stocuser",
    "pk": 2,
    "fields": {
      "password": "pbkdf2_sha256$...",  # Generated via Django
      "username": "ion",
      "email": "ion@example.com",
      "first_name": "Ion",
      "last_name": "Popescu",
      "is_staff": false,
      "is_active": true,
      "is_readonly": false,
      "date_joined": "2024-06-09T00:00:00Z",
      "last_login": null
    }
  },
  {
    "model": "stoc.userpreferences",
    "pk": 2,
    "fields": {
      "user": 2,
      "default_nava": 978,
      "default_tragator": "ION",
      "default_data": "2024-06-09"
    }
  }
]
```

Load in container:

```bash
python manage.py loaddata apps/stoc/fixtures/initial_users.json
```

---

## Post-Deployment (After CI/CD Deploy)

```bash
# Run migrations
kubectl exec deployment/django-stoc -n default -- python manage.py migrate

# Create superuser (if not exists)
kubectl exec deployment/django-stoc -n default -- python manage.py createsuperuser
```

---

## User Types in Stoc App

| Type | is_readonly | Can do |
|------|------------|---------|
| **Full Access** | ✓ False | Data entry, expeditions, edit, delete, export |
| **Read-Only** | ✓ True | View rapoarte, export — NO data entry |
| **Staff** | is_staff=True | Merge la /admin/, manage users |

---

## Per-User Preferences (NEW — cu UserPreferences model)

Fiecare user are propria setare:
- **Navă implicită** — la login, loadează aceasta navă
- **Tractator implicit** — name auto-filled în forms

Exemplu — User "costel":
- Login → Nava 978, Tractator "COSTEL" auto-loaded
- User "ion":
- Login → Nava 980, Tractator "ION" auto-loaded

Preferințele se salvează persistent (DB) — nu dispar dacă browser se închide!

---

## Migration Steps (After Code Update)

1. **Commit code changes**
   ```bash
   git add django_app/apps/stoc/models.py
   git add django_app/apps/stoc/admin.py
   git add django_app/apps/stoc/migrations/0002_userpreferences.py
   git commit -m "Add UserPreferences model for per-user settings"
   git push origin main
   ```

2. **CI/CD auto-triggers (Woodpecker)**
   - Builds image
   - Pushes to registry
   - Updates K8s manifest

3. **K3s auto-deploys (ArgoCD)**
   - Pulls new image
   - Pod restarts

4. **Migration runs (startup script)**
   ```bash
   python manage.py migrate --noinput
   ```
   → Creates `stoc_user_preferences` table

5. **Done!**
   - Users can login
   - Their preferences auto-created on first login
   - Can customize in UI ("Settings" button)

---

## Exemplu Workflow — Add New User "RARES"

### Admin Panel:
1. Go to `/admin/`
2. Users → Add User
3. Username: `rares`, Password: (generate)
4. Check "Active", Uncheck "Read-only"
5. Save
6. Preferințe utilizator → Add
7. User: Rares, Nava: 979, Tractator: "RARES"
8. Save

### User Login:
1. Navigate to `/` (auto-redirect to /login/)
2. Username: `rares`, Password: (created)
3. Redirects to index
4. Nava 979 pre-selected
5. Tragator "RARES" pre-filled
6. User can change via Settings button

---

## Troubleshooting

**User can't login?**
```bash
# Check if active
python manage.py shell
>>> from apps.stoc.models import StocUser
>>> u = StocUser.objects.get(username='rares')
>>> u.is_active
True  # Should be True
```

**Preferences not loading?**
```bash
# Check if preferences exist
>>> from apps.stoc.models import UserPreferences
>>> prefs = UserPreferences.objects.get(user=u)
>>> prefs.default_nava
979
```

**Preferences not persisting after CI/CD deploy?**
- Ensure migration ran: `python manage.py migrate`
- Check DB: `psql -d stoc_db -c "SELECT * FROM stoc_user_preferences;"`

---

## Summary

✅ **StocUser** — Django built-in auth (username/password)
✅ **is_readonly** — Role-based permissions (full access vs read-only)
✅ **UserPreferences** — Per-user persistent settings (nava, tragator)

Add user via Admin → Preferences auto-create → User logs in → Settings loaded from DB!
