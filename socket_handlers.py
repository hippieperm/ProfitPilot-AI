import eventlet
import atexit
from flask import current_app, request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from models import db, Transaction, StockPrice, StockHolding, User, PriceHistory
from datetime import datetime, timedelta
import threading
import time

# 가격 업데이트 스레드 상태 관리
price_update_thread = None
stop_event = threading.Event()

def init_socket_handlers(socketio, stock_data, app):
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        with app.app_context():
            if current_user.is_authenticated:
                join_room(f'user_{current_user.id}')
                # 현재 페이지 확인
                current_page = request.args.get('page', '')

                if current_page == 'leaderboard':
                    leaderboard_data = get_leaderboard_data()
                    socketio.emit('market_data', {
                        'leaderboard': leaderboard_data,
                        'total_users': User.query.count()
                    }, room=f'user_{current_user.id}')
                elif current_page == 'home':
                    stocks = stock_data.get_all_stocks()
                    total_users = User.query.count()
                    active_users = User.query.filter(
                        User.last_login > datetime.utcnow() - timedelta(minutes=30)
                    ).count()

                    recent_trades = Transaction.query.order_by(
                        Transaction.timestamp.desc()
                    ).limit(10).all()

                    major_trades = Transaction.query.filter(
                        Transaction.quantity >= 1000
                    ).order_by(Transaction.timestamp.desc()).limit(10).all()

                    socketio.emit('market_data', {
                        'stocks': stocks,
                        'total_users': total_users,
                        'active_users': active_users,
                        'recent_trades': [trade.to_dict() for trade in recent_trades],
                        'major_trades': [trade.to_dict() for trade in major_trades]
                    }, room=f'user_{current_user.id}')
                else:
                    stocks = stock_data.get_all_stocks()
                    holdings = get_user_holdings()
                    socketio.emit('market_data', {
                        'stocks': stocks,
                        'holdings': holdings
                    }, room=f'user_{current_user.id}')
            else:
                stocks = stock_data.get_all_stocks()
                socketio.emit('market_data', {
                    'stocks': stocks
                })

    @socketio.on('disconnect')
    def handle_disconnect():
        try:
            print('Client disconnected')
            if current_user.is_authenticated:
                leave_room(f'user_{current_user.id}')
        except Exception as e:
            print(f"Error in handle_disconnect: {str(e)}")
