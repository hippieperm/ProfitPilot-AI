import os

class Config:
    SECRET_KEY = 'your-secret-key'
    DEBUG = True

    # 기본 설정
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', 'csrf-key-please-change')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///stock_game.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 챗봇 설정
    OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', 'http://localhost:11434')
    OLLAMA_MODEL = 'llama3:8b' # LLM 모델
    num_ctx = 4096  # 컨텍스트 크기

    # 서버 안정성 관련 설정
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 1800

    # 세션 설정
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # 데이터 디렉토리 설정
    DATA_DIR = 'data'
    BACKUP_DIR = os.path.join(DATA_DIR, 'backup')

    # 파일 경로 설정
    USERS_FILE = os.path.join(DATA_DIR, 'users.json')
    STOCKS_FILE = os.path.join(DATA_DIR, 'stocks.json')
    PORTFOLIOS_FILE = os.path.join(DATA_DIR, 'portfolios.json')
    TRADES_FILE = os.path.join(DATA_DIR, 'trades.json')
    HISTORY_FILE = os.path.join(DATA_DIR, 'price_history.json')
    
    # 사용자 관련 설정
    INITIAL_BALANCE = 10000000  # 초기 자금
    MAX_USERS = 1000  # 최대 사용자 수
    MIN_USERNAME_LENGTH = 4  # 최소 사용자명 길이
    MIN_PASSWORD_LENGTH = 6  # 최소 비밀번호 길이
    
    # 백업 관련 설정
    MAX_BACKUP_COUNT = 5  # 보관할 최대 백업 파일 수
    BACKUP_INTERVAL = 3600  # 백업 주기 (초)

    @staticmethod
    def init_app(app):
        """앱 초기화 시 필요한 디렉토리 생성"""
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.BACKUP_DIR, exist_ok=True) 