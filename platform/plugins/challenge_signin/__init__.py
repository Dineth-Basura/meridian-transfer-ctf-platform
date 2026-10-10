"""Require a live session before serving challenge attachments.

CTFd's private visibility permits signed download tokens without a session;
this local policy closes that exception for Meridian Transfer challenge files.
"""
from flask import abort, g, redirect, request, url_for
from CTFd.models import Files
from CTFd.utils.user import authed
from CTFd.utils.security.auth import logout_user

def load(app):
    @app.before_request
    def remember_auth_state():
        if request.endpoint in ('auth.register', 'auth.login'):
            g.meridian_was_authed = authed()

    @app.after_request
    def redirect_account_flow(response):
        # Only change successful form submissions that created a new session.
        if (request.method != 'POST'
                or request.endpoint not in ('auth.register', 'auth.login')
                or getattr(g, 'meridian_was_authed', True)
                or response.status_code not in (302, 303)
                or not authed()):
            return response
        if request.endpoint == 'auth.register':
            logout_user()
            return redirect(url_for('auth.login'))
        return redirect(url_for('challenges.listing'))

    @app.before_request
    def require_signin_for_challenge_file():
        if request.endpoint != 'views.files' or authed():
            return
        path = (request.view_args or {}).get('path', '')
        if path and Files.query.filter_by(location=path, type='challenge').first():
            abort(403)
