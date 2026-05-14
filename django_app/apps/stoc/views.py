from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from django.http import HttpResponse
from datetime import date
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

DEFAULT_SHIP = 978
DEFAULT_TRAGATOR = "COSTEL"

ALL_FIELDS = [
    "Nava", "Nr Lista", "ID Lista", "Locatie", "Lungime",
    "Nr Cabluri", "Dosar", "Tragator", "Data", "Data trimisa",
    "Trimis", "Rework", "Data Rework", "Ore Rework"
]

FIELD_TYPES = {
    "Nava": "numeric", "Nr Lista": "text", "ID Lista": "text",
    "Locatie": "text", "Lungime": "numeric", "Nr Cabluri": "numeric",
    "Dosar": "text", "Tragator": "text", "Data": "date",
    "Data trimisa": "date", "Trimis": "boolean", "Rework": "boolean",
    "Data Rework": "date", "Ore Rework": "numeric"
}


def _get_locatii(nava):
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT DISTINCT "Locatie" FROM list963 WHERE "Nava" = %s AND "Locatie" IS NOT NULL ORDER BY "Locatie"',
            [nava]
        )
        return [row[0] for row in cursor.fetchall()]


def _rows_to_dicts(cursor, cols):
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _make_excel(rows, headers, sheet_name, summary=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name

    header_fill = PatternFill("solid", fgColor="1a1c23")
    header_font = Font(bold=True, color="af7c4c")

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')

    for row_idx, row in enumerate(rows, 2):
        for col_idx, val in enumerate(row, 1):
            ws.cell(row=row_idx, column=col_idx, value=val)

    if summary:
        last_row = len(rows) + 3
        for idx, (k, v) in enumerate(summary.items()):
            ws.cell(row=last_row, column=idx + 1, value=f"{k}: {v}")

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────────────────────────────────────
# Introducere Date
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def index(request):
    nava = int(request.session.get('last_nava', DEFAULT_SHIP))
    tragator = request.session.get('last_tragator', DEFAULT_TRAGATOR)
    today = date.today()

    if request.method == 'POST':
        action = request.POST.get('action', 'save')

        if action == 'settings':
            request.session['last_nava'] = int(request.POST.get('nava', DEFAULT_SHIP))
            request.session['last_tragator'] = request.POST.get('tragator', DEFAULT_TRAGATOR)
            return redirect('stoc:index')

        nr_lista = request.POST.get('nr_lista', '').strip()
        id_lista = request.POST.get('id_lista', '').strip()
        locatie = request.POST.get('loc_manual', '').strip() or request.POST.get('loc_select', '')
        lungime_raw = request.POST.get('lungime', '').strip()
        nr_cabluri_raw = request.POST.get('nr_cabluri', '').strip()
        data_str = request.POST.get('data', str(today))

        if not all([nr_lista, id_lista, locatie, lungime_raw, nr_cabluri_raw]):
            messages.error(request, "Toate câmpurile sunt obligatorii!")
        else:
            try:
                lungime = float(lungime_raw.replace(',', '.'))
                nr_cabluri = int(nr_cabluri_raw)
                with connection.cursor() as cursor:
                    cursor.execute('''
                        INSERT INTO list963
                        ("Nava","Nr Lista","ID Lista","Locatie","Lungime","Nr Cabluri","Data","Tragator","Trimis")
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ''', [nava, nr_lista, id_lista, locatie, lungime, nr_cabluri, data_str, tragator, False])
                messages.success(request, f"Salvat: {id_lista} — {data_str}")
                return redirect('stoc:index')
            except ValueError:
                messages.error(request, "Lungime și Nr Cabluri trebuie să fie numere valide!")

    locatii = _get_locatii(nava)

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT "Nr Lista","Locatie","Nr Cabluri","Lungime","ID Lista"
            FROM list963 WHERE "Data" = %s
            ORDER BY "Locatie" ASC, "Nr Lista" ASC
        ''', [today])
        cols = ['nr_lista', 'locatie', 'nr_cabluri', 'lungime', 'id_lista']
        today_entries = _rows_to_dicts(cursor, cols)

    total_m = sum(float(e['lungime'] or 0) for e in today_entries)
    total_c = sum(int(e['nr_cabluri'] or 0) for e in today_entries)

    return render(request, 'stoc/index.html', {
        'locatii': locatii,
        'today': today,
        'today_entries': today_entries,
        'total_m': int(total_m),
        'total_c': total_c,
        'total_l': len(today_entries),
        'last_nava': nava,
        'last_tragator': tragator,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Expediție
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def expeditie(request):
    today = date.today()

    if request.method == 'POST':
        ids = request.POST.getlist('selected_ids')
        dosar = request.POST.get('dosar', '').strip()
        data_exp = request.POST.get('data_expediere', str(today))

        if not dosar:
            messages.error(request, "Introdu numele dosarului!")
        elif not ids:
            messages.error(request, "Selectează cel puțin o listă!")
        else:
            ids_int = [int(i) for i in ids]
            with connection.cursor() as cursor:
                cursor.execute('''
                    UPDATE list963 SET "Trimis"=TRUE, "Data trimisa"=%s, "Dosar"=%s
                    WHERE "ID" = ANY(%s::int[])
                ''', [data_exp, dosar, ids_int])
            messages.success(request, f"Liste marcate pentru expediție în dosarul {dosar}!")
            return redirect('stoc:expeditie')

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT "ID","Nr Lista","Locatie","Lungime","Nr Cabluri"
            FROM list963
            WHERE ("Trimis" IS NOT TRUE) AND ("Rework" IS NOT TRUE) AND "Nava" = 978
            ORDER BY "Nr Lista" ASC
        ''')
        cols = ['id', 'nr_lista', 'locatie', 'lungime', 'nr_cabluri']
        records = _rows_to_dicts(cursor, cols)

    return render(request, 'stoc/expeditie.html', {'records': records, 'today': today})


# ─────────────────────────────────────────────────────────────────────────────
# Rapoarte
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def rapoarte(request):
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT "Nr Lista","Locatie","Lungime","Nr Cabluri"
            FROM list963 WHERE "Data" = CURRENT_DATE
            ORDER BY "Locatie" ASC, "Nr Lista" ASC
        ''')
        azi = _rows_to_dicts(cursor, ['nr_lista', 'locatie', 'lungime', 'nr_cabluri'])

        cursor.execute('''
            SELECT COALESCE(SUM("Lungime"),0), COALESCE(SUM("Nr Cabluri"),0), COUNT(*)
            FROM list963 WHERE "Data" >= DATE_TRUNC('week', CURRENT_DATE)
        ''')
        row = cursor.fetchone()
        sapt_sumar = {'metri': int(row[0]), 'cabluri': int(row[1]), 'liste': int(row[2])}

        cursor.execute('''
            SELECT "Data", SUM("Lungime"), SUM("Nr Cabluri"), COUNT(*)
            FROM list963 GROUP BY "Data" ORDER BY "Data" DESC
        ''')
        zile = _rows_to_dicts(cursor, ['data', 'metri', 'cabluri', 'liste'])

        cursor.execute('''
            SELECT COALESCE(SUM("Lungime"),0), COALESCE(SUM("Nr Cabluri"),0), COUNT(*)
            FROM list963 WHERE DATE_TRUNC('month',"Data") = DATE_TRUNC('month',CURRENT_DATE)
        ''')
        row = cursor.fetchone()
        luna_sumar = {'metri': int(row[0]), 'cabluri': int(row[1]), 'liste': int(row[2])}

        cursor.execute('''
            SELECT EXTRACT(YEAR FROM "Data")::INT, EXTRACT(WEEK FROM "Data")::INT,
                   SUM("Lungime"), SUM("Nr Cabluri"), COUNT(*)
            FROM list963 GROUP BY 1,2 ORDER BY 1 DESC, 2 DESC
        ''')
        saptamani = _rows_to_dicts(cursor, ['an', 'nr_sapt', 'metri', 'cabluri', 'liste'])

        cursor.execute('''
            SELECT "Nr Lista","ID Lista","Locatie","Lungime","Nr Cabluri",
                   "Data","Tragator","Trimis","Data trimisa","Nava","Dosar","Rework","Data Rework","Ore Rework"
            FROM list963 WHERE "Nava" = 978 ORDER BY "Nr Lista" ASC
        ''')
        nava = _rows_to_dicts(cursor, ['nr_lista','id_lista','locatie','lungime','nr_cabluri',
                                        'data','tragator','trimis','data_trimisa','nava','dosar',
                                        'rework','data_rework','ore_rework'])

        cursor.execute('''
            SELECT "Nr Lista","ID Lista","Locatie","Lungime","Nr Cabluri","Data trimisa","Dosar"
            FROM list963 WHERE "Nava" = 978 AND "Trimis" = true ORDER BY "Nr Lista" ASC
        ''')
        trimise = _rows_to_dicts(cursor, ['nr_lista','id_lista','locatie','lungime','nr_cabluri','data_trimisa','dosar'])

        cursor.execute('''
            SELECT "Nr Lista","ID Lista","Locatie","Lungime","Nr Cabluri","Rework"
            FROM list963 WHERE "Nava" = 978 AND "Trimis" = false ORDER BY "Nr Lista" ASC
        ''')
        hala = _rows_to_dicts(cursor, ['nr_lista','id_lista','locatie','lungime','nr_cabluri','rework'])

        cursor.execute('''
            SELECT "Nr Lista","ID Lista","Locatie","Lungime","Nr Cabluri","Data Rework","Ore Rework"
            FROM list963 WHERE "Nava" = 978 AND "Rework" = true ORDER BY "Nr Lista" ASC
        ''')
        rework = _rows_to_dicts(cursor, ['nr_lista','id_lista','locatie','lungime','nr_cabluri','data_rework','ore_rework'])

        cursor.execute('''
            SELECT "Nava", SUM("Lungime"), SUM("Nr Cabluri"), COUNT(*)
            FROM list963 GROUP BY "Nava" ORDER BY "Nava" ASC
        ''')
        all_time = _rows_to_dicts(cursor, ['nava','lungime_totala','cabluri_total','numar_liste'])

    def _sum(lst, key):
        return sum(float(r[key] or 0) for r in lst)

    return render(request, 'stoc/rapoarte.html', {
        'azi': azi,
        'azi_sumar': {'metri': int(_sum(azi,'lungime')), 'cabluri': int(_sum(azi,'nr_cabluri')), 'liste': len(azi)},
        'sapt_sumar': sapt_sumar,
        'zile': zile,
        'luna_sumar': luna_sumar,
        'saptamani': saptamani,
        'nava': nava,
        'nava_sumar': {'metri': int(_sum(nava,'lungime')), 'cabluri': int(_sum(nava,'nr_cabluri')), 'liste': len(nava)},
        'trimise': trimise,
        'trimise_sumar': {'metri': int(_sum(trimise,'lungime')), 'cabluri': int(_sum(trimise,'nr_cabluri')), 'liste': len(trimise)},
        'hala': hala,
        'hala_sumar': {'metri': int(_sum(hala,'lungime')), 'cabluri': int(_sum(hala,'nr_cabluri')), 'liste': len(hala)},
        'rework': rework,
        'rework_sumar': {'metri': int(_sum(rework,'lungime')), 'cabluri': int(_sum(rework,'nr_cabluri')), 'liste': len(rework)},
        'all_time': all_time,
        'all_time_sumar': {'metri': int(_sum(all_time,'lungime_totala')), 'cabluri': int(_sum(all_time,'cabluri_total')), 'liste': int(_sum(all_time,'numar_liste'))},
    })


# ─────────────────────────────────────────────────────────────────────────────
# Super Vizualizare
# ─────────────────────────────────────────────────────────────────────────────

OPERATORS_SQL = {"=": "=", "≠": "!=", ">": ">", "<": "<", "≥": ">=", "≤": "<="}

def _build_query(conditions, vis_cols, sort_field, sort_dir):
    col_sql = ", ".join([f'"{c}"' for c in vis_cols])
    where_parts, params = [], []

    for cond in conditions:
        field = cond.get('field', 'Nava')
        op = cond.get('op', '=')
        val = cond.get('val', '')
        ft = FIELD_TYPES.get(field, 'text')

        col = f'"{field}"'

        if op == 'conține':
            where_parts.append(f'{col} ILIKE %s')
            params.append(f'%{val}%')
        elif op in ('= True', '= False'):
            where_parts.append(f'{col} IS {"TRUE" if op == "= True" else "FALSE"}')
        elif ft == 'numeric' and val:
            try:
                where_parts.append(f'{col} {OPERATORS_SQL.get(op,"=")} %s')
                params.append(float(val.replace(',', '.')))
            except ValueError:
                pass
        elif val:
            where_parts.append(f'{col} {OPERATORS_SQL.get(op,"=")} %s')
            params.append(val)

    where_sql = f'WHERE {" AND ".join(where_parts)}' if where_parts else ''
    order_sql = f'ORDER BY "{sort_field}" {sort_dir}' if sort_field else ''
    query = f'SELECT "ID", {col_sql} FROM list963 {where_sql} {order_sql}'
    return query, params


@login_required
def superviz(request):
    DEFAULT_COLS = ["Nr Lista", "ID Lista", "Lungime", "Nr Cabluri", "Data"]

    if request.method == 'POST':
        action = request.POST.get('action', 'query')

        if action == 'edit':
            ids = [int(i) for i in request.POST.getlist('selected_ids')]
            updates = {}
            field_map = {
                'nr_lista': 'Nr Lista', 'id_lista': 'ID Lista', 'locatie': 'Locatie',
                'dosar': 'Dosar', 'tragator': 'Tragator',
            }
            for key, col in field_map.items():
                val = request.POST.get(key, '').strip()
                if val:
                    updates[col] = val
            for key, col in [('lungime', 'Lungime'), ('ore_rework', 'Ore Rework')]:
                val = request.POST.get(key, '').strip()
                if val:
                    try:
                        updates[col] = float(val.replace(',', '.'))
                    except ValueError:
                        pass
            val = request.POST.get('nr_cabluri', '').strip()
            if val:
                try:
                    updates['Nr Cabluri'] = int(val)
                except ValueError:
                    pass
            for key, col in [('data', 'Data'), ('data_trimisa', 'Data trimisa'), ('data_rework', 'Data Rework')]:
                val = request.POST.get(key, '').strip()
                if val:
                    updates[col] = val
            for key, col in [('trimis', 'Trimis'), ('rework', 'Rework')]:
                val = request.POST.get(key, '')
                if val in ('True', 'False'):
                    updates[col] = val == 'True'
            if updates and ids:
                set_parts = [f'"{col}" = %s' for col in updates]
                params = list(updates.values()) + [ids]
                with connection.cursor() as cursor:
                    cursor.execute(
                        f'UPDATE list963 SET {", ".join(set_parts)} WHERE "ID" = ANY(%s::int[])',
                        params
                    )
                messages.success(request, f"{len(ids)} înregistrări actualizate.")
            return redirect('stoc:superviz')

        if action == 'delete':
            ids = [int(i) for i in request.POST.getlist('selected_ids')]
            if ids:
                with connection.cursor() as cursor:
                    cursor.execute('DELETE FROM list963 WHERE "ID" = ANY(%s::int[])', [ids])
                messages.success(request, f"{len(ids)} înregistrări șterse.")
            return redirect('stoc:superviz')

    # Build conditions from GET params
    conditions = []
    i = 0
    while True:
        field = request.GET.get(f'cf_{i}')
        if field is None:
            break
        conditions.append({
            'field': field,
            'op': request.GET.get(f'co_{i}', '='),
            'val': request.GET.get(f'cv_{i}', ''),
        })
        i += 1

    if not conditions:
        conditions = [{'field': 'Nava', 'op': '=', 'val': '978'}]

    vis_cols_param = request.GET.get('cols', '')
    vis_cols = vis_cols_param.split(',') if vis_cols_param else DEFAULT_COLS
    vis_cols = [c for c in vis_cols if c in ALL_FIELDS] or DEFAULT_COLS

    sort_field = request.GET.get('sort_field', 'Nr Lista')
    if sort_field not in ALL_FIELDS:
        sort_field = 'Nr Lista'
    sort_dir = 'DESC' if request.GET.get('sort_dir', 'ASC') == 'DESC' else 'ASC'

    query, params = _build_query(conditions, vis_cols, sort_field, sort_dir)

    results = []
    headers = ['ID'] + vis_cols
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            results = [dict(zip(headers, row)) for row in cursor.fetchall()]
    except Exception as e:
        messages.error(request, f"Eroare interogare: {e}")

    total_m = sum(float(r.get('Lungime') or 0) for r in results)
    total_c = sum(int(r.get('Nr Cabluri') or 0) for r in results)

    return render(request, 'stoc/superviz.html', {
        'results': results,
        'headers': vis_cols,
        'conditions': conditions,
        'vis_cols': vis_cols,
        'all_fields': ALL_FIELDS,
        'sort_field': sort_field,
        'sort_dir': sort_dir,
        'total_m': int(total_m),
        'total_c': total_c,
        'total_l': len(results),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Export Excel
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def export_excel(request, tip):
    tip_map = {
        'azi': ('Raport_Azi', 'SELECT "Nr Lista","Locatie","Lungime","Nr Cabluri" FROM list963 WHERE "Data" = CURRENT_DATE ORDER BY "Locatie","Nr Lista"', ['Nr Lista','Locatie','Lungime','Nr Cabluri']),
        'nava': ('Registru_978', 'SELECT "Nr Lista","ID Lista","Locatie","Lungime","Nr Cabluri","Data","Tragator","Trimis","Dosar" FROM list963 WHERE "Nava"=978 ORDER BY "Nr Lista"', ['Nr Lista','ID Lista','Locatie','Lungime','Nr Cabluri','Data','Tragator','Trimis','Dosar']),
        'trimise': ('Liste_Trimise', 'SELECT "Nr Lista","ID Lista","Locatie","Lungime","Nr Cabluri","Data trimisa","Dosar" FROM list963 WHERE "Nava"=978 AND "Trimis"=true ORDER BY "Nr Lista"', ['Nr Lista','ID Lista','Locatie','Lungime','Nr Cabluri','Data trimisa','Dosar']),
        'hala': ('Stoc_Hala', 'SELECT "Nr Lista","ID Lista","Locatie","Lungime","Nr Cabluri" FROM list963 WHERE "Nava"=978 AND "Trimis"=false ORDER BY "Nr Lista"', ['Nr Lista','ID Lista','Locatie','Lungime','Nr Cabluri']),
        'rework': ('Rework', 'SELECT "Nr Lista","ID Lista","Locatie","Lungime","Nr Cabluri","Data Rework","Ore Rework" FROM list963 WHERE "Nava"=978 AND "Rework"=true ORDER BY "Nr Lista"', ['Nr Lista','ID Lista','Locatie','Lungime','Nr Cabluri','Data Rework','Ore Rework']),
    }

    if tip not in tip_map:
        return HttpResponse("Export invalid", status=400)

    filename, query, cols = tip_map[tip]
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    buffer = _make_excel(rows, cols, filename)
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    return response
