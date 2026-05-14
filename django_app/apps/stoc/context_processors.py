from django.db import connection


def active_nava(request):
    if not request.user.is_authenticated:
        return {}
    nava = int(request.session.get('last_nava', 978))
    try:
        with connection.cursor() as c:
            c.execute('SELECT DISTINCT "Nava" FROM list963 WHERE "Nava" IS NOT NULL ORDER BY "Nava"')
            nave = [row[0] for row in c.fetchall()]
    except Exception:
        nave = [nava]
    return {
        'active_nava': nava,
        'available_nave': nave,
        'is_readonly': getattr(request.user, 'is_readonly', False),
    }
