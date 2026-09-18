import os
from pathlib import Path
from flask import Flask, render_template, send_from_directory, session, redirect, url_for
from config import Config
from services.settings_service import get_company_settings

def create_app(config_class=Config):
    """Application factory for Employee Digital Profile & QR Review System."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize upload directories
    config_class.init_app(app)

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp, api_bp
    from routes.qr import qr_bp
    from routes.analytics import analytics_bp
    from routes.ai import ai_bp
    from routes.lead import lead_bp
    from routes.employee import employee_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(qr_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(lead_bp)
    app.register_blueprint(employee_bp)  # Registered last for /<slug> dynamic catch-all

    # Uploads file server route
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(str(Config.UPLOAD_PATH), filename)

    # Home route redirect
    @app.route('/')
    def index():
        if 'admin_id' in session:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('auth.login'))

    # Global template context
    @app.context_processor
    def inject_global_context():
        try:
            settings = get_company_settings()
        except Exception:
            settings = {
                'company_name': 'Apex Innovations',
                'primary_color': '#4f46e5',
                'secondary_color': '#06b6d4'
            }
        return {
            'company_settings': settings,
            'current_admin': session.get('admin_name'),
            'base_url': Config.BASE_URL
        }

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        try:
            settings = get_company_settings()
        except Exception:
            settings = None
        return render_template('public/404.html', settings=settings), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        try:
            settings = get_company_settings()
        except Exception:
            settings = None
        return render_template('public/500.html', settings=settings), 500

    return app

app = create_app()

if __name__ == '__main__':
    print(f"Starting Employee Digital Profile & QR Review System...")
    print(f"Local Server URL: {Config.BASE_URL}")
    print(f"Admin Portal: {Config.BASE_URL}/admin/login")
    app.run(host='0.0.0.0', port=5000, debug=True)
