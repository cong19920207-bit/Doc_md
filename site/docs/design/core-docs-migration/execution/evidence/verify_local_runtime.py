import json, secrets, hashlib, ssl, socket
from pathlib import Path
from collections import Counter
from urllib.parse import quote
import httpx
from app import settings
from app.auth_store import AuthStore, ROLE_USER_ID, ROLE_SUPER_ID
from app.chunking import scan_briefs

base = 'http://web'
headers = {'Host':'127.0.0.1:18765', 'Origin':'http://127.0.0.1:18765'}
auth = AuthStore()
created = []
report = {'checks': [], 'fixtures_cleaned': False}

def check(label, response, expected):
    status = response.status_code
    report['checks'].append({'label': label, 'status': status, 'expected': expected})
    assert status == expected, (label, status, expected)
    assert 'Index of /' not in response.text[:500], label
    return response

try:
    clients = {'anonymous': httpx.Client(base_url=base, headers=headers, timeout=15)}
    for role, role_id in [('user', ROLE_USER_ID), ('admin', ROLE_SUPER_ID)]:
        name = 'migration-' + role + '-' + secrets.token_hex(4)
        pw = secrets.token_urlsafe(24)
        row = auth.create_account(name, pw, role_id)
        created.append((row['id'], name))
        client = httpx.Client(base_url=base, headers=headers, timeout=15)
        check(role + ' login', client.post('/api/kb/auth/login', json={'username':name,'password':pw}), 200)
        me = check(role + ' identity', client.get('/api/kb/auth/me'), 200).json()
        assert bool(me.get('is_super', me.get('account', {}).get('is_super'))) == (role == 'admin'), me.keys()
        clients[role] = client

    admin = clients['admin']
    manifest = check('projected manifest', admin.get('/prd/llm-manifest.json'), 200).json()
    assert all(p.startswith('prd/') for p in manifest['scan_roots'])
    assert 'site/core-docs/' not in json.dumps(manifest)
    paths = manifest['published_paths']
    image = next(p for p in paths if p.lower().endswith('.png'))
    history_index = next(p for p in paths if p.endswith('/history/index.json') and admin.get('/'+p).json()['files'])
    histories = admin.get('/'+history_index).json()['files']
    assert all(p in paths for p in histories)
    readable = ['/feature-interaction/', '/prd/llm-manifest.json', '/prd/design/referral/PRD.md',
                '/prd/design/referral/brief/current.md', '/prd/design/referral/changelog.md',
                '/' + image, '/' + history_index, '/' + histories[0], '/admin-skin-demo/',
                '/reviews/referral/summary/index.html']
    private = ['/INDEX.md', '/llm-manifest.json', '/workspace/INDEX.md', '/knowledge/INDEX.md',
               '/site/docs/INDEX.md', '/docs/INDEX.md', '/site/.env', '/.git/config', '/.env',
               '/site/kb-api/app/main.py', '/site/docker-compose.yml', '/site/docker/nginx.conf',
               '/lkonw.com_nginx.tar', '/lkonw.com_nginx/key.pem', '/tls/key.pem', '/data/kb-config.json',
               '/site/core-docs/prd/INDEX.md', '/prd/archive/', '/prd/inbox/entries/private.md',
               '/prd/../workspace/INDEX.md', '/prd/%2e%2e/workspace/INDEX.md', '/unknown-route']
    for role, client in clients.items():
        check(role+' login page', client.get('/login/'), 200)
        for root in ['/', '/site', '/site/']:
            res = check(role+' root '+root, client.get(root), 302)
            assert res.headers['location'] == '/feature-interaction/'
        for path in readable:
            res = check(role+' '+path, client.get(quote(path, safe='/%')), 302 if role=='anonymous' else 200)
            if role=='anonymous': assert res.headers['location'].startswith('/login/?next=')
        check(role+' admin page', client.get('/kb-admin/'), {'anonymous':302,'user':403,'admin':200}[role])
        check(role+' admin API', client.get('/api/kb/admin/accounts'), {'anonymous':401,'user':403,'admin':200}[role])
        res = check(role+' legacy admin', client.get('/site/kb-admin/'), 302)
        assert res.headers['location'] == '/kb-admin/'
        for path in private:
            res = client.get(path)
            # Anonymous may be sent to login before static lookup. No role gets the file.
            assert res.status_code in ({302,403,404} if role=='anonymous' else {403,404}), (role,path,res.status_code)
            report['checks'].append({'label':role+' private '+path,'status':res.status_code})
        for path in ['/prd/', '/prd/design/', '/prd/design/referral/history/']:
            res=client.get(path)
            check(role+' no listing '+path,res,302 if role=='anonymous' else 403)

    # Every generated URL can be read through the actual authenticated Nginx gate.
    failed=[]
    for path in paths:
        res=admin.head('/'+quote(path, safe='/'))
        if res.status_code != 200: failed.append([path,res.status_code])
    report['published_urls']={'count':len(paths),'failed':failed}
    assert not failed, failed[:10]

    chunks=scan_briefs()
    report['scan']={'chunks':len(chunks),'features':len({c.feature_id for c in chunks}),
                    'logical_prefixes':sorted({c.path.split('/')[0] for c in chunks})}
    # Fetch real old citation coordinates, without exposing questions, replies, or credentials.
    with auth.repo._conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT c_gen FROM qa_rounds WHERE c_gen IS NOT NULL AND JSON_LENGTH(c_gen)>0 ORDER BY created_at DESC LIMIT 20")
            citations=[]
            for row in cur.fetchall():
                value=row['c_gen']
                citations.extend(json.loads(value) if isinstance(value,str) else value)
    valid={(c.path,c.chunk_id):c for c in chunks}
    old=next((c for c in citations if (c.get('path'),c.get('chunk_id')) in valid and c.get('content_hash')==valid[c['path'],c['chunk_id']].content_hash), None)
    sample=old or chunks[0].as_dict()
    params={k:sample[k] for k in ['path','chunk_id','content_hash']}
    res=check('existing citation read',clients['user'].get('/api/kb/chunk',params=params),200)
    assert res.json()['content_hash']==params['content_hash']
    bad=dict(params, content_hash='not-current')
    check('stale citation hash',clients['user'].get('/api/kb/chunk',params=bad),409)
    report['citation']={'from_saved_conversation':old is not None,'path':params['path'],'chunk_id':params['chunk_id']}

    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname=False
    ctx.verify_mode=ssl.CERT_NONE  # Local dummy certificate handshake test; no browser trust bypass.
    with socket.create_connection(('web',443),timeout=10) as sock:
        with ctx.wrap_socket(sock,server_hostname='localhost') as tls:
            report['tls']={'handshake':True,'version':tls.version(),'certificate_sha256':hashlib.sha256(tls.getpeercert(binary_form=True)).hexdigest()}
    report['health']=admin.get('/api/kb/health').json()
    assert report['health']['index_ready'] and not report['health']['startup_error']
finally:
    for account_id,name in created:
        with auth.repo._conn() as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM kb_sessions WHERE account_id=%s',(account_id,))
                cur.execute('DELETE FROM kb_login_locks WHERE username=%s',(name,))
                cur.execute('DELETE FROM kb_accounts WHERE id=%s',(account_id,))
    report['fixtures_cleaned']=True
    print(json.dumps(report,ensure_ascii=False,indent=2))
