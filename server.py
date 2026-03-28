"""
Play Reviewer — Flask backend (complete fix)

Architecture:
- date_from is passed INTO the scraper (early-stop optimization)
- max_count = reviews to COLLECT within the date range (not raw fetch limit)
- Scraper stops when: collected >= max_count  OR  review.date < date_from  OR  no more pages
- date_to applied in post_process (reviews newer than date_to are skipped but don't stop scraping)
- rating filter applied in post_process
- keyword filter applied in post_process

This means:
  Son 6 ay with max=5000 → fetches until 5000 reviews found within last 6 months OR no more pages
  Son 12 ay with max=5000 → fetches until 5000 reviews found within last 12 months OR no more pages
  → DIFFERENT results for different date ranges ✓
  
  max=5000 vs max=10000 with same date range → fetches until respective limits
  → DIFFERENT counts ✓
"""

from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd, io, re, time, uuid, threading, traceback, random
from datetime import datetime, date, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

app  = Flask(__name__)
JOBS = {}
LOCK = threading.Lock()

# ── helpers ────────────────────────────────────────────────────────────────────

def cs(s, fb=''):
    """Clean string — never None."""
    return str(s).strip() if s is not None else fb

def safe_float(v, fb=0.0):
    try: return round(float(v or 0), 1)
    except: return fb

def sid(appId):
    """Safe DOM element id from appId — replaces all non-alphanumeric."""
    return re.sub(r'[^a-zA-Z0-9]', '_', str(appId or 'app'))

def extract_id(text):
    text = cs(text)
    m = re.search(r'id=([a-zA-Z0-9._]+)', text)
    if m: return m.group(1)
    if re.match(r'^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$', text):
        return text
    return None

def get_app_info(app_id):
    from google_play_scraper import app as G
    for c in ['us', 'gb', 'au']:
        try:
            d = G(app_id, lang='en', country=c)
            aid = cs(d.get('appId') or app_id)
            if not aid: continue
            return dict(appId=aid, title=cs(d.get('title'), aid),
                        developer=cs(d.get('developer')), score=safe_float(d.get('score')),
                        icon=cs(d.get('icon')), installs=cs(d.get('installs')))
        except Exception as e:
            print(f"app_info {app_id}/{c}: {e}")
    return None

def do_search(query):
    from google_play_scraper import search
    seen, out = set(), []
    # Try English and Turkish language/country combos — covers globally popular apps
    combos = [('en','us'), ('en','gb'), ('en','tr'), ('tr','tr')]
    for lang, c in combos:
        try:
            res = search(query, lang=lang, country=c, n_hits=15)
            for r in res:
                aid = cs(r.get('appId'))
                if not aid or aid in seen: continue
                seen.add(aid)
                out.append(dict(appId=aid, title=cs(r.get('title')),
                                developer=cs(r.get('developer')),
                                score=safe_float(r.get('score')),
                                icon=cs(r.get('icon'))))
        except Exception as e:
            print(f"search '{query}'/{lang}/{c}: {e}")
    # If still nothing, try treating the query itself as a direct app ID
    if not out:
        info = get_app_info(query.strip())
        if info:
            out.append(info)
    return out[:20]

# ── CORE SCRAPER ───────────────────────────────────────────────────────────────

def scrape_app(app_id, title, max_collect, date_from, job_id):
    """
    Fetch reviews until max_collect reviews are collected within date_from boundary.
    Tries multiple countries to maximise coverage (important for globally popular apps like Cambly).
    Deduplicates by reviewId across countries.
    """
    from google_play_scraper import reviews, Sort

    COUNTRY_LANG = {
        'us': 'en', 'gb': 'en', 'au': 'en', 'ca': 'en',
        'in': 'en', 'nz': 'en', 'ie': 'en', 'za': 'en',
    }
    COUNTRIES = list(COUNTRY_LANG.keys())

    seen_ids    = set()
    rows        = []
    fetched_total = 0
    remaining   = max_collect  # rolls over unused quota to next country

    for country in COUNTRIES:
        if remaining <= 0:
            break

        # Each country gets an equal share; unused quota rolls to the next country
        country_quota = remaining // max(1, len(COUNTRIES) - COUNTRIES.index(country))
        country_collected = 0
        token = None
        date_boundary_hit = False

        print(f"[{app_id}] country={country} quota={country_quota}, "
              f"total so far={len(rows)}/{max_collect}")

        while country_collected < country_quota:
            result = None

            for attempt in range(4):
                if attempt > 0:
                    time.sleep([2, 5, 10][attempt - 1])
                try:
                    result, token = reviews(
                        app_id, lang=COUNTRY_LANG[country], country=country,
                        sort=Sort.NEWEST, count=200,
                        continuation_token=token,
                    )
                    break
                except Exception as e:
                    print(f"[{app_id}] attempt {attempt+1}/4 country={country}: {e}")

            if result is None:
                print(f"[{app_id}] all retries failed for country={country}")
                break
            if not result:
                print(f"[{app_id}] no more pages for country={country}")
                break

            fetched_total += len(result)

            for r in result:
                rid = cs(r.get('reviewId'))

                at = r.get('at')
                if at and at.tzinfo is None:
                    at = at.replace(tzinfo=timezone.utc)

                # DATE EARLY STOP: reviews are newest-first within a country
                if date_from and at and at.date() < date_from:
                    date_boundary_hit = True
                    break

                # Deduplicate across countries
                if rid and rid in seen_ids:
                    continue
                if rid:
                    seen_ids.add(rid)

                rep = r.get('repliedAt')
                if rep and rep.tzinfo is None:
                    rep = rep.replace(tzinfo=timezone.utc)

                rows.append(dict(
                    app_id       = app_id,
                    app_name     = title,
                    yorum_id     = rid,
                    kullanici    = cs(r.get('userName')),
                    puan         = int(r.get('score') or 0),
                    yorum        = cs(r.get('content')),
                    tarih        = at,
                    begeni       = int(r.get('thumbsUpCount') or 0),
                    uygulama_ver = cs(r.get('reviewCreatedVersion')),
                    cevap        = cs(r.get('replyContent')),
                    cevap_tarihi = rep,
                ))
                country_collected += 1

                if country_collected >= country_quota:
                    break

            print(f"[{app_id}] country={country} got={country_collected}, "
                  f"total={len(rows)}, date_stop={date_boundary_hit}, "
                  f"token={'yes' if token else 'no'}")

            with LOCK:
                if job_id in JOBS:
                    JOBS[job_id]['prog'][app_id] = dict(fetched=len(rows), done=False)

            if date_boundary_hit or token is None or country_collected >= country_quota:
                break

            time.sleep(0.5)

        # Unused quota from this country rolls over to remaining countries
        remaining -= country_collected

    with LOCK:
        if job_id in JOBS:
            JOBS[job_id]['prog'][app_id] = dict(fetched=len(rows), done=True)

    random.shuffle(rows)
    print(f"[{app_id}] DONE: {len(rows)} collected (fetched {fetched_total} raw, "
          f"{len(seen_ids)} unique IDs across {len(COUNTRIES)} countries)")
    return rows


# ── POST PROCESSING ────────────────────────────────────────────────────────────

def post_process(raw, date_from, date_to, rating, keywords, kw_and):
    """
    Final filters - ALL applied here as the authoritative gate.
    The scraper early-stop on date_from is only an optimisation.
    """
    out = []
    for r in raw:
        at = r['tarih']

        # date_from - guaranteed filter regardless of scraper behaviour
        if date_from and at and at.date() < date_from:
            continue

        # date_to
        if date_to and at and at.date() > date_to:
            continue

        # rating filter
        if rating and r['puan'] != rating:
            continue

        # keyword scoring + filter
        kw_hit, kw_list = 0, []
        if keywords:
            txt = r['yorum'].lower()
            for k in keywords:
                if k.lower() in txt:
                    kw_hit += 1
                    kw_list.append(k)
            if kw_and:
                if kw_hit < len(keywords): continue   # AND: all must match
            else:
                if kw_hit == 0: continue              # OR: at least one must match

        at_v  = r['tarih']
        rep_v = r['cevap_tarihi']
        out.append(dict(
            app_id       = r['app_id'],
            app_name     = r['app_name'],
            yorum_id     = r['yorum_id'],
            kullanici    = r['kullanici'],
            puan         = r['puan'],
            yorum        = r['yorum'],
            tarih        = at_v.isoformat()  if at_v  else '',
            begeni       = r['begeni'],
            uygulama_ver = r['uygulama_ver'],
            cevap        = r['cevap'],
            cevap_tarihi = rep_v.isoformat() if rep_v else '',
            kw_eslesme   = kw_hit,
            kw_listesi   = ', '.join(kw_list[:30]),
        ))
    return out


# ── WORKER ────────────────────────────────────────────────────────────────────

def _worker(app_dict, start_delay, max_collect, date_from, job_id):
    """Proper named function — avoids lambda closure issues."""
    if start_delay > 0:
        time.sleep(start_delay)
    return scrape_app(
        app_dict['appId'], app_dict['title'],
        max_collect, date_from, job_id
    )


def run_job(job_id, apps, max_collect, rating, date_from, date_to, keywords, kw_and):
    try:
        with LOCK:
            JOBS[job_id]['status'] = 'running'

        raw_all = []
        with ThreadPoolExecutor(max_workers=min(len(apps), 4)) as exe:
            futs = {
                exe.submit(_worker, a, i * 2, max_collect, date_from, job_id): a['appId']
                for i, a in enumerate(apps)
            }
            for f in as_completed(futs):
                aid = futs[f]
                try:
                    raw_all.extend(f.result())
                except Exception as e:
                    print(f"[{aid}] worker error: {e}\n{traceback.format_exc()}")

        print(f"[job] raw: {len(raw_all)}, post-processing…")
        filtered = post_process(raw_all, date_from, date_to, rating, keywords, kw_and)
        print(f"[job] final: {len(filtered)} "
              f"(date_from={date_from}, date_to={date_to}, kw={len(keywords)}, "
              f"{'AND' if kw_and else 'OR'})")

        with LOCK:
            JOBS[job_id].update(
                status   = 'done',
                results  = filtered,
                raw_count= len(raw_all),
                kw_count = len(keywords),
            )

    except Exception as e:
        print(f"[job] FATAL: {e}\n{traceback.format_exc()}")
        with LOCK:
            JOBS[job_id].update(status='error', error=str(e), results=[], raw_count=0)


# ── ROUTES ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/lookup', methods=['POST'])
def lookup():
    try:
        d = request.get_json(force=True) or {}
        q = cs(d.get('query'))
        if not q: return jsonify(error='Arama terimi boş olamaz.'), 400
        aid = extract_id(q)
        if aid:
            info = get_app_info(aid)
            if info: return jsonify(type='single', result=info)
            return jsonify(error='Uygulama bulunamadı.'), 404
        results = do_search(q)
        if results: return jsonify(type='search', results=results)
        return jsonify(error='Sonuç bulunamadı.'), 404
    except Exception as e:
        return jsonify(error=f'Sunucu hatası: {e}'), 500


@app.route('/api/scrape/start', methods=['POST'])
def scrape_start():
    try:
        d = request.get_json(force=True) or {}

        # Validate apps
        apps = [dict(appId=cs(a.get('appId')), title=cs(a.get('title')))
                for a in (d.get('apps') or []) if cs(a.get('appId'))]
        if not apps:
            return jsonify(error='En az bir geçerli uygulama gerekli.'), 400

        # max_collect = how many reviews to collect per app within date range
        max_collect = 5000
        try: max_collect = min(max(int(d.get('max_count') or 5000), 10), 100000)
        except: pass

        rating = None
        try:
            rv = d.get('rating')
            if rv: rating = int(rv)
        except: pass

        preset   = cs(d.get('date_preset'), 'custom')
        keywords = [cs(k) for k in (d.get('keywords') or []) if cs(k)]
        kw_and   = bool(d.get('kw_mode_and'))

        today = date.today()
        pm = {'last7':7,'last30':30,'last90':90,'last180':180,'last365':365}
        if preset in pm:
            date_from = today - timedelta(days=pm[preset])
            date_to   = today
        else:
            date_from = date_to = None
            try:
                s = cs(d.get('date_from'))
                if s: date_from = date.fromisoformat(s)
            except: pass
            try:
                s = cs(d.get('date_to'))
                if s: date_to = date.fromisoformat(s)
            except: pass

        job_id = str(uuid.uuid4())
        with LOCK:
            JOBS[job_id] = dict(
                status   = 'queued',
                prog     = {a['appId']: dict(fetched=0, done=False) for a in apps},
                results  = None,
                raw_count= 0,
                kw_count = len(keywords),
                error    = None,
                # Store params for display
                params   = dict(max_collect=max_collect, date_from=str(date_from),
                                date_to=str(date_to), kw_count=len(keywords)),
            )

        threading.Thread(
            target=run_job,
            args=(job_id, apps, max_collect, rating, date_from, date_to, keywords, kw_and),
            daemon=True,
        ).start()

        return jsonify(job_id=job_id)

    except Exception as e:
        print(f"/api/scrape/start error: {e}\n{traceback.format_exc()}")
        return jsonify(error=f'Sunucu hatası: {e}'), 500


@app.route('/api/scrape/status/<job_id>')
def scrape_status(job_id):
    with LOCK: job = JOBS.get(job_id)
    if not job: return jsonify(error='Job bulunamadı.'), 404
    return jsonify(
        status       = job['status'],
        prog         = job['prog'],
        total_fetched= sum(p['fetched'] for p in job['prog'].values()),
        error        = job.get('error'),
        params       = job.get('params', {}),
    )


@app.route('/api/scrape/results/<job_id>')
def scrape_results(job_id):
    with LOCK: job = JOBS.get(job_id)
    if not job: return jsonify(error='Job bulunamadı.'), 404
    if job['status'] not in ('done', 'error'):
        return jsonify(error='Henüz bitmedi.'), 400
    return jsonify(
        count    = len(job.get('results') or []),
        raw_count= job.get('raw_count', 0),
        kw_count = job.get('kw_count', 0),
        data     = job.get('results') or [],
        error    = job.get('error'),
        params   = job.get('params', {}),
    )


@app.route('/api/scrape/download/<job_id>/<fmt>')
def download(job_id, fmt):
    try:
        with LOCK: job = JOBS.get(job_id)
        if not job or job['status'] != 'done':
            return jsonify(error='Henüz bitmedi.'), 400
        data = list(job.get('results') or [])
        if not data: return jsonify(error='İndirilecek veri yok.'), 400

        df = pd.DataFrame(data)
        for col in ['tarih', 'cevap_tarihi']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], utc=True, errors='coerce').dt.tz_localize(None)

        ts = datetime.now().strftime('%Y%m%d_%H%M')
        W  = dict(app_id=22,app_name=22,kullanici=18,puan=7,yorum=62,tarih=18,
                  begeni=9,kw_eslesme=13,kw_listesi=55,uygulama_ver=14,
                  cevap=40,cevap_tarihi=18,yorum_id=32)

        if fmt == 'csv':
            buf = io.BytesIO()
            df.to_csv(buf, index=False, encoding='utf-8-sig')
            buf.seek(0)
            return send_file(buf, mimetype='text/csv',
                             download_name=f'yorumlar_{ts}.csv', as_attachment=True)

        if fmt == 'excel':
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as wr:
                wb  = wr.book
                hdr = wb.add_format(dict(bold=True,bg_color='#01875f',
                                         font_color='#fff',border=1,text_wrap=True))
                cel = wb.add_format(dict(border=1,text_wrap=True,valign='top'))

                if 'app_name' in df.columns:
                    smry = (df.groupby('app_name')
                            .agg(yorum=('yorum','count'),ort_puan=('puan','mean'),
                                 kw_hit=('kw_eslesme','sum'))
                            .round(2).reset_index())
                    smry.to_excel(wr, sheet_name='Özet', index=False)
                    ws0 = wr.sheets['Özet']
                    for ci, col in enumerate(smry.columns):
                        ws0.write(0,ci,col,hdr); ws0.set_column(ci,ci,24)

                    for aname, grp in df.groupby('app_name'):
                        sn = re.sub(r'[\\/*?:\[\]]','_',str(aname))[:28]
                        grp.to_excel(wr, sheet_name=sn, index=False, startrow=1)
                        ws = wr.sheets[sn]
                        for ci, col in enumerate(grp.columns):
                            ws.write(0,ci,col,hdr); ws.set_column(ci,ci,W.get(col,16),cel)
                        ws.freeze_panes(2,0)
                        ws.autofilter(1,0,len(grp)+1,len(grp.columns)-1)

                df.to_excel(wr, sheet_name='Tüm Veriler', index=False, startrow=1)
                ws2 = wr.sheets['Tüm Veriler']
                for ci, col in enumerate(df.columns):
                    ws2.write(0,ci,col,hdr); ws2.set_column(ci,ci,W.get(col,16))
                ws2.freeze_panes(2,0)
                ws2.autofilter(1,0,len(df)+1,len(df.columns)-1)

                if job['kw_count']:
                    kdf = df[df['kw_eslesme']>0]
                    if not kdf.empty:
                        kdf.to_excel(wr, sheet_name='Keyword Eslesenler', index=False, startrow=1)
                        ws3 = wr.sheets['Keyword Eslesenler']
                        for ci, col in enumerate(kdf.columns):
                            ws3.write(0,ci,col,hdr); ws3.set_column(ci,ci,W.get(col,16))
                        ws3.freeze_panes(2,0)
                        ws3.autofilter(1,0,len(kdf)+1,len(kdf.columns)-1)

            buf.seek(0)
            return send_file(buf,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                download_name=f'yorumlar_{ts}.xlsx', as_attachment=True)

        return jsonify(error='Geçersiz format.'), 400

    except Exception as e:
        print(f"/api/scrape/download error: {e}\n{traceback.format_exc()}")
        return jsonify(error=str(e)), 500


@app.route('/api/keywords/parse', methods=['POST'])
def parse_kw():
    try:
        f = request.files.get('file')
        if not f: return jsonify(error='Dosya bulunamadı.'), 400
        df = (pd.read_csv(f,header=None) if f.filename.lower().endswith('.csv')
              else pd.read_excel(f,header=None))
        kws = df.iloc[:,0].dropna().astype(str).str.strip().tolist()
        kws = [k for k in kws if k and k.lower() not in ('keyword','anahtar kelime','nan','')][:500]
        return jsonify(keywords=kws, count=len(kws))
    except Exception as e:
        return jsonify(error=f'Dosya okunamadı: {e}'), 400


@app.route('/api/keywords/template')
def kw_template():
    buf = io.BytesIO()
    pd.DataFrame({'keyword':['crash','bug','slow','update','great','love',
                              'hate','fix','terrible','amazing','freeze','login']}).to_excel(buf,index=False)
    buf.seek(0)
    return send_file(buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        download_name='keyword_sablonu.xlsx', as_attachment=True)


if __name__ == '__main__':
    import webbrowser, os
    port = int(os.environ.get('PORT', 8080))
    print(f'''
┌──────────────────────────────────────────────┐
│  📱 Play Reviewer  →  http://localhost:{port}  │
│  lang=en, country=us → global English        │
│  date_from passed to scraper (early-stop)    │
│  max_count = reviews to collect in range     │
└──────────────────────────────────────────────┘
''')
    webbrowser.open(f'http://localhost:{port}')
    app.run(port=port, debug=False, threaded=True)
