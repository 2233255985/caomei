import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'data.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MODEL_PATH = os.path.join(BASE_DIR, 'models', 'best_strawberry.onnx')
    CLASSES_PATH = os.path.join(BASE_DIR, 'models', 'classes.txt')
    DEFAULT_BACKEND = 'local'
    ATLAS_URL = 'http://192.168.1.2:6800'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    VIDEO_FOLDER = os.path.join(BASE_DIR, 'videos')
    ANNOTATED_FOLDER = os.path.join(BASE_DIR, 'annotated')
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
    BATCH_MAX_FILES = 100
