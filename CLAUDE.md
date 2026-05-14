# CLAUDE.md — Gestiune Cabluri (Streamlit → Django rewrite)

## Contextul sesiunii curente

**Scopul:** Rescriem această aplicație Streamlit ca modul Django integrat în proiectul `e:\docker\online_food_management`, pe branch-ul `feature/stoc`.

Utilizatorii aplicației Django Lotus vor putea accesa modulul de stoc cabluri direct din interfața web, fără aplicație Streamlit separată.

---

## Proiectul Django țintă

- **Locație:** `e:\docker\online_food_management`
- **Branch:** `feature/stoc` (deja creat și pushat pe `origin/feature/stoc`)
- **GitHub:** `x3m444/djangolotus`
- **Framework:** Django 4.2, PostgreSQL (Supabase), Bootstrap 5 + Bootswatch, HTMX
- **URL prefix:** `/staff/stoc/`
- **Django namespace:** `stoc`
- **App Django de creat:** `apps/stoc/`

### Fișiere cheie Django deja existente:
- `lotus/settings.py` — INSTALLED_APPS, DB config
- `lotus/urls.py` — URL root
- `templates/base/base.html` — navbar cu roluri (admin, receptie, bucatarie, ghiseu, livrator)
- Roluri existente: `admin`, `receptie`, `bucatarie`, `ghiseu`, `livrator`
- `requirements.txt` conține deja: `xlsxwriter`, `openpyxl`, `psycopg2-binary`

---

## Arhitectura Streamlit existentă

```bash
# Rulare aplicație
streamlit run app.py
```

| Modul | Rol |
|---|---|
| `app.py` | Entry point: page config, auth gate, DB integrity check, sidebar nav routing |
| `config.py` | Constante — DEFAULT_SHIP=978, DEFAULT_TRAGATOR="COSTEL", REPORT_TABS (8 tab-uri) |
| `database.py` | SQLAlchemy engine (cached via `@lru_cache`), funcții CRUD: get_locations_for_ship, insert_cable_record, update_records, delete_records |
| `auth.py` | Single-password auth via `st.secrets["password"]` + cookie HMAC |
| `forms.py` | "Introducere Date" (data entry) + "Expediție" (marcare trimis) |
| `reports.py` | 8 tab-uri raport: Azi/Săptămână/Lună/Navă/Trimise/Hală/Rework/All Time |
| `super_viz.py` | Query builder dinamic, multi-row select, bulk edit, bulk delete |
| `utils.py` | Export Excel xlsxwriter, validate_numeric_input, dataframe styling |

---

## Baza de date

**IMPORTANT:** Tabelul `list963` există deja pe Supabase și servește aplicația Streamlit curentă. **NU se modifică structura tabelului.**

### Tabelul `list963` — coloane exacte (cu majuscule/spații):

| Coloană PostgreSQL | Tip | Note |
|---|---|---|
| `ID` | SERIAL PK | cheie primară |
| `Nr Lista` | TEXT | numărul listei |
| `ID Lista` | TEXT | identificator listă |
| `Locatie` | TEXT | locația cablului |
| `Lungime` | NUMERIC | metri |
| `Nr Cabluri` | INTEGER | număr cabluri |
| `Nava` | INTEGER | numărul navei (default 978) |
| `Tragator` | TEXT | persoana (default "COSTEL") |
| `Data` | DATE | data înregistrării |
| `Trimis` | BOOLEAN | marcat ca expediat |
| `Data trimisa` | DATE | data expedierii |
| `Dosar` | TEXT | număr dosar expediere |
| `Rework` | BOOLEAN | necesită relucrare |
| `Data Rework` | DATE | data rework |
| `Ore Rework` | NUMERIC | ore de rework |

### Model Django (managed=False — NU se rulează migrate pentru el):
```python
class Cable(models.Model):
    id = models.AutoField(primary_key=True, db_column='ID')
    nr_lista = models.TextField(null=True, blank=True, db_column='Nr Lista')
    id_lista = models.TextField(null=True, blank=True, db_column='ID Lista')
    locatie = models.TextField(null=True, blank=True, db_column='Locatie')
    lungime = models.FloatField(null=True, blank=True, db_column='Lungime')
    nr_cabluri = models.IntegerField(null=True, blank=True, db_column='Nr Cabluri')
    nava = models.IntegerField(null=True, blank=True, db_column='Nava')
    tragator = models.TextField(null=True, blank=True, db_column='Tragator')
    data = models.DateField(null=True, blank=True, db_column='Data')
    trimis = models.BooleanField(null=True, blank=True, default=False, db_column='Trimis')
    data_trimisa = models.DateField(null=True, blank=True, db_column='Data trimisa')
    dosar = models.TextField(null=True, blank=True, db_column='Dosar')
    rework = models.BooleanField(null=True, blank=True, default=False, db_column='Rework')
    data_rework = models.DateField(null=True, blank=True, db_column='Data Rework')
    ore_rework = models.FloatField(null=True, blank=True, db_column='Ore Rework')

    class Meta:
        managed = False
        db_table = 'list963'
```

---

## Module de implementat

### 1. Introducere Date — view `index` → `/staff/stoc/`
- Sursă Streamlit: `forms.py → show_data_entry_form()` + `show_today_entries()`
- Formular: Nr Lista, ID Lista, Locatie (select din DB + opțiune "altă locație" manual), Lungime, Nr Cabluri, Nava (default 978), Tragator (default "COSTEL"), Data (default azi)
- Locatii se preiau dinamic: `SELECT DISTINCT "Locatie" FROM list963 WHERE "Locatie" IS NOT NULL ORDER BY "Locatie"`
- Tabel cu înregistrările de azi (Data = CURRENT_DATE) cu totaluri

### 2. Expeditie — view `expeditie` → `/staff/stoc/expeditie/`
- Sursă Streamlit: `forms.py → show_expedition_form()`
- Lista înregistrărilor netrimise Nava=978 (Trimis=FALSE sau NULL)
- Selectare multiplă → marcare Trimis=TRUE cu Dosar + Data trimisa

### 3. Rapoarte — view `rapoarte` → `/staff/stoc/rapoarte/`
- Sursă Streamlit: `reports.py → show_reports_section()`
- 8 tab-uri Bootstrap randate server-side (fără caching, direct SQL):
  - **Azi** — `WHERE "Data" = CURRENT_DATE` — totaluri + tabel
  - **Săptămână** — totaluri săptămâna curentă + jurnal zilnic descrescător
  - **Lună** — totaluri luna curentă + istoric pe săptămâni
  - **Navă** — toate coloanele pentru Nava=978, sortat după Nr Lista
  - **Trimise** — Nava=978 AND Trimis=TRUE
  - **Hală** — Nava=978 AND Trimis=FALSE (rămase)
  - **Rework** — Nava=978 AND Rework=TRUE
  - **All Time** — GROUP BY Nava, totaluri per navă
- Export Excel per tab (openpyxl)

### 4. Super Vizualizare — view `superviz` → `/staff/stoc/superviz/`
- Sursă Streamlit: `super_viz.py → show_super_visualization()`
- Form cu condiții dinamice (câmp + operator + valoare), max 5-6 condiții
- Coloane vizibile selectabile (multiselect)
- Sortare (câmp + direcție ASC/DESC)
- Default la încărcare: Nava=978, sort Nr Lista ASC
- Rezultate cu totaluri (metri, cabluri, liste)
- Export Excel
- Bulk edit (câmpuri opționale, doar cele completate se salvează)
- Bulk delete (checkbox confirmare)

---

## Structura fișierelor de creat în `e:\docker\online_food_management`

```
apps/stoc/
├── __init__.py
├── apps.py           → StocConfig, name='apps.stoc'
├── models.py         → class Cable (managed=False)
├── views.py          → index, expeditie, rapoarte, superviz, export_excel
├── urls.py           → 4 URL-uri + export
└── forms.py          → CableForm, ExpeditieForm, SuperVizForm

templates/stoc/
├── index.html        → Introducere Date + tabel azi
├── expeditie.html    → marcare trimis
├── rapoarte.html     → 8 tab-uri Bootstrap
└── superviz.html     → query builder + bulk edit/delete
```

### Modificări în fișierele existente:
```python
# lotus/settings.py — adaugă în INSTALLED_APPS:
'apps.stoc',

# lotus/urls.py — adaugă:
path('staff/stoc/', include('apps.stoc.urls', namespace='stoc')),

# templates/base/base.html — adaugă link în navbar pentru rol 'admin' și 'stoc':
# (în blocul {% if rol == 'admin' %} sau separat {% elif rol == 'stoc' %})
```

---

## Decizii tehnice

1. **managed=False** — tabelul există, Django nu îl creează/modifică
2. **Raw SQL** cu `django.db.connection.cursor()` pentru rapoarte complexe (GROUP BY, DATE_TRUNC, etc.)
3. **ORM** pentru insert, update by ID, delete by ID simplu
4. **Excel export** — openpyxl (deja în requirements.txt)
5. **Auth** — rol nou `stoc` + `admin` poate accesa modulul
6. **Nu se folosesc** pandas, SQLAlchemy, Streamlit în versiunea Django

---

## Ce s-a făcut deja pe branch feature/stoc

- Branch creat și pushat pe origin
- `schema.sql` — script creare tabele PostgreSQL (pentru instalare fresh)
- `install.sh` — script verbose instalare/update pe server Oracle
- `templates/core/manual.html` + `MANUAL_UTILIZARE.md` — manual utilizare

## Ce rămâne de făcut

1. Crea `apps/stoc/` complet
2. Actualiza `settings.py`, `urls.py`, `base.html`
3. Crea toate templatele Bootstrap
4. Commit + push pe `feature/stoc`

---

## Mediu și comenzi utile

```bash
# Verificare branch curent
cd e:\docker\online_food_management
git branch --show-current   # trebuie să fie feature/stoc

# Rulare locală (necesită .env cu credențiale DB)
python manage.py runserver

# Push după implementare
git add apps/stoc/ templates/stoc/ lotus/settings.py lotus/urls.py templates/base/base.html
git commit -m "feat(stoc): modul gestiune cabluri Django"
git push origin feature/stoc
```

## Secrets necesare în `.env` (deja configurat pe server)

```
DB_NAME=...
DB_USER=...
DB_PASS=...
DB_HOST=...
DB_PORT=5432
SECRET_KEY=...
ALLOWED_HOSTS=lotus.incercari.duckdns.org,127.0.0.1,localhost
DEBUG=False
AUTH_ENABLED=True
```
