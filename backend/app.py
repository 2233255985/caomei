import os
from flask import Flask, current_app, send_from_directory
from flask_cors import CORS
from config import Config
from extensions import db


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    CORS(app, origins=['http://localhost:3000', 'http://localhost:5173'])
    db.init_app(app)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['VIDEO_FOLDER'], exist_ok=True)
    os.makedirs(app.config['ANNOTATED_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'models'), exist_ok=True)

    with app.app_context():
        from models.detect_record import DetectRecord
        db.create_all()

    from routes.detect import detect_bp
    from routes.stats import stats_bp
    from routes.settings import settings_bp
    app.register_blueprint(detect_bp, url_prefix='/api/detect')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        upload_dir = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(upload_dir, filename)

    @app.route('/videos/<filename>')
    def uploaded_video(filename):
        return send_from_directory(current_app.config['VIDEO_FOLDER'], filename)

    @app.route('/annotated/<filename>')
    def annotated_file(filename):
        return send_from_directory(current_app.config['ANNOTATED_FOLDER'], filename)

    return app


if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=debug)
