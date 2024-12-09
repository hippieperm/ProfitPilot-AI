# LangChain 관련 임포트를 먼저
from chatbot import PersonalityBot

# eventlet monkey patching
import eventlet
eventlet.monkey_patch()

# 나머지 임포트
from routes import main, auth
from flask import Flask, current_app, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_migrate import Migrate
from models import db, User, StockHolding, StockPrice, PriceHistory

from socket_handlers import init_socket_handlers
from stock_data import stock_data  # StockData 클래스 대신 인스턴스 import
from filters import init_filters

import os
import atexit
import signal
from datetime import datetime, timedelta

def create_app():
    app = Flask(__name__)
    
    # 설정
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY', 'csrf-key-please-change')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///stock_game.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.update(
        SQLALCHEMY_POOL_SIZE=10,
        SQLALCHEMY_MAX_OVERFLOW=20,
        SQLALCHEMY_POOL_TIMEOUT=30,
        SQLALCHEMY_POOL_RECYCLE=1800,
        
        PERMANENT_SESSION_LIFETIME=timedelta(days=31),
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True
    )

    # PersonalityBot 인스턴스 생성 및 등록
    app.chatbot = PersonalityBot()

    # 블루프린트 등록
    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app

app = create_app()

# 데이터베이스 초기화
db.init_app(app)

# 마이그레이션 설정
migrate = Migrate(app, db)

# 로그인 매니저 설정
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = '로그인이 필요한 페이지입니다.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

# 필터 초기화
init_filters(app)

# 소켓IO 설정
socketio = SocketIO(
    app,
    ping_timeout=60,
    ping_interval=25,
    cors_allowed_origins=["http://localhost:5000", "http://127.0.0.1:5000"],
    async_mode='eventlet',
    logger=False,
    engineio_logger=False
)

# 템플릿 필터
@app.template_filter('format_number')
def format_number(value):
    if value is None:
        return '0'
    try:
        if isinstance(value, str):
            value = float(value.replace(',', ''))
        return "{:,}".format(float(value))
    except (ValueError, TypeError, AttributeError):
        return '0'

@app.template_filter('format_percentage')
def format_percentage(value):
    if value is None:
        return '0.00%'
    try:
        if isinstance(value, str):
            value = float(value.replace('%', '').replace(',', ''))
        return "{:.2f}%".format(float(value))
    except (ValueError, TypeError, AttributeError):
        return '0.00%'

# StockData 설정
with app.app_context():
    # 데이터베이스 테이블 생성
    db.create_all()
    
    # StockData 초기화
    stock_data.app = app
    stock_data.socketio = socketio
    stock_data.initialize_db()
    
    # 챗봇 초기화를 app_context 내부로 이동
    chatbot = PersonalityBot()
    app.chatbot = chatbot  # 앱 객체에 챗봇 인스턴스 저장

# 소켓 핸들러 초기화
init_socket_handlers(socketio, stock_data, app)

# 가격 업데이트 시작
stock_data.start_price_update_thread()

# 종료 처리
def cleanup_handler(signum=None, frame=None):
    print("Server shutting down...")
    try:
        # 가격 업데이트 중지
        stock_data.stop_price_updates()
        print("Price updates stopped")
        
        # 데이터베이스 연결 정리
        try:
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
            print("Database connections cleaned up")
        except Exception as db_error:
            print(f"Error cleaning up database: {str(db_error)}")
        
        # 소켓IO 연결 종료
        try:
            if socketio:
                socketio.stop()
            print("SocketIO stopped")
        except Exception as socket_error:
            print(f"Error stopping SocketIO: {str(socket_error)}")
        
        print("Cleanup completed")
    except Exception as e:
        print(f"Error in cleanup: {str(e)}")
    finally:
        # 정상 종료
        try:
            os._exit(0)
        except:
            pass

# 종료 핸들러 등록
atexit.register(cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)
signal.signal(signal.SIGINT, cleanup_handler)


if __name__ == '__main__':
    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # 파일 변경 감지 비활성화
        )
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, shutting down...")
        cleanup_handler()
    except Exception as e:
        print(f"Server error: {str(e)}")
        cleanup_handler()
