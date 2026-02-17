# FarmIntel - Smart Farming & Crop Intelligence System
# Main Flask Application

import os
from pathlib import Path
from flask import Flask, redirect
from config import Config
from db import init_db

# Create upload folders if not exist (Windows-safe)
for folder in ('static/uploads', 'static/uploads/crops', 'static/uploads/products'):
    Path(folder).mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config.from_object(Config)
init_db(app)

# Register blueprints
from routes.auth import auth_bp
from routes.farmer import farmer_bp
from routes.admin_routes import admin_bp
from routes.crops import crops_bp
from routes.schemes import schemes_bp
from routes.store import store_bp
from routes.financial import financial_bp

app.register_blueprint(auth_bp)
app.register_blueprint(farmer_bp, url_prefix='/farmer')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(crops_bp, url_prefix='/crops')
app.register_blueprint(schemes_bp, url_prefix='/schemes')
app.register_blueprint(store_bp, url_prefix='/store')
app.register_blueprint(financial_bp, url_prefix='/financial')

@app.route('/')
def index():
    return redirect('/farmer/login')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
