from flask import Flask

from db import close_db
from routes.auth import auth_bp
from routes.dbmanager import dbmanager_bp
from routes.manager import manager_bp
from routes.player import player_bp
from routes.referee import referee_bp

app = Flask(__name__)
app.secret_key = 'transferdb-cmpe321-secret-2026'
app.teardown_appcontext(close_db)
app.jinja_env.globals['enumerate'] = enumerate

app.register_blueprint(auth_bp)
app.register_blueprint(player_bp, url_prefix='/player')
app.register_blueprint(manager_bp, url_prefix='/manager')
app.register_blueprint(referee_bp, url_prefix='/referee')
app.register_blueprint(dbmanager_bp, url_prefix='/dbmanager')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
