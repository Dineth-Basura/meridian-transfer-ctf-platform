"""Local educational release register. /export intentionally omits owner check."""
import hmac
import os
import secrets
from datetime import timedelta
from functools import wraps
from flask import Flask, abort, redirect, render_template, request, session, url_for, Response
from db import user_by_name, user_by_id, owned_releases, release_by_id
from seed import verify_password


def export_allowed(record, user_id, *, enforce_owner: bool) -> bool:
    """Private fixed comparison sets enforce_owner=True; live export uses False."""
    return record is not None and (not enforce_owner or record['owner_id'] == user_id)

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get('MT04_SESSION_SECRET'),
        SEED_DB_PATH=os.environ.get('MT04_DB_PATH','/app/data/seed.sqlite'),
        SESSION_COOKIE_NAME='mt04_session',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=False,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
    )
    if test_config:
        app.config.update(test_config)
    if not app.config['SECRET_KEY']:
        raise RuntimeError('MT04_SESSION_SECRET is required')

    def current_user():
        uid = session.get('user_id')
        return user_by_id(uid) if isinstance(uid,int) else None
    def login_required(func):
        @wraps(func)
        def wrapper(*args,**kwargs):
            if not current_user():
                return redirect(url_for('login'))
            return func(*args,**kwargs)
        return wrapper
    def csrf_token():
        if 'csrf_token' not in session:
            session['csrf_token']=secrets.token_urlsafe(24)
        return session['csrf_token']
    def valid_csrf():
        actual=request.form.get('csrf_token','')
        expected=session.get('csrf_token','')
        return bool(actual and expected) and hmac.compare_digest(actual,expected)
    app.jinja_env.globals['csrf_token']=csrf_token

    @app.get('/healthz')
    def healthz():
        return Response('ok\n',mimetype='text/plain')
    @app.get('/')
    def index():
        return redirect(url_for('releases') if current_user() else url_for('login'))
    @app.route('/login',methods=['GET','POST'])
    def login():
        if current_user(): return redirect(url_for('releases'))
        error=None
        if request.method=='POST':
            if not valid_csrf():
                abort(400)
            username=request.form.get('username','')
            password=request.form.get('password','')
            user=user_by_name(username)
            if user and verify_password(password,user['password_hash']):
                session.clear()
                session['user_id']=user['id']
                session['csrf_token']=secrets.token_urlsafe(24)
                session.permanent=True
                return redirect(url_for('releases'))
            error='Invalid training credentials.'
        return render_template('login.html',error=error)
    @app.post('/logout')
    @login_required
    def logout():
        if not valid_csrf(): abort(400)
        session.clear()
        return redirect(url_for('login'))
    @app.get('/releases')
    @login_required
    def releases():
        user=current_user()
        return render_template('releases.html',user=user,records=owned_releases(user['id']))
    @app.get('/release/<int:record_id>')
    @login_required
    def release(record_id):
        user=current_user(); record=release_by_id(record_id)
        if record is None or record['owner_id']!=user['id']:
            abort(404)
        return render_template('release.html',record=record)
    @app.get('/export/<int:record_id>')
    @login_required
    def export(record_id):
        user=current_user(); record=release_by_id(record_id)
        if not export_allowed(record,user['id'],enforce_owner=False):
            abort(404)
        # Intentional, single educational flaw: no record.owner_id comparison here.
        body=(f"MERIDIAN TRANSFER / RELEASE EXPORT\nRecord: {record['id']}\nReference: {record['transfer_reference']}\n"
              f"Status: {record['release_status']}\n\n{record['export_note']}")
        return Response(body,mimetype='text/plain',headers={'Content-Disposition':f'attachment; filename="release-{record_id}.txt"','Cache-Control':'no-store'})
    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def error(error):
        return render_template('error.html',code=error.code),error.code
    @app.after_request
    def safety_headers(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
        return response
    return app

app=create_app()
