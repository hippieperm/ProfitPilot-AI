import eventlet
import atexit
from flask import current_app, request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from models import db, Transaction, StockPrice, StockHolding, User, PriceHistory
from datetime import datetime, timedelta
import threading
import time
#from chatbot import PersonalityBot  # 클래스만 임포트

# 가격 업데이트 스레드 상태 관리
price_update_thread = None
stop_event = threading.Event()

# 전역 변수로 bot 인스턴스 생성
#bot = PersonalityBot()

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
                    # 리더보드 페이지인 경우 리더보드 데이터만 전송
                    leaderboard_data = get_leaderboard_data()
                    socketio.emit('market_data', {
                        'leaderboard': leaderboard_data,
                        'total_users': User.query.count()
                    }, room=f'user_{current_user.id}')
                elif current_page == 'home':
                    # 홈 페이지인 경우 모든 데이터 전송
                    stocks = stock_data.get_all_stocks()
                    total_users = User.query.count()
                    active_users = User.query.filter(
                        User.last_login > datetime.utcnow() - timedelta(minutes=30)
                    ).count()
                    
                    # 최근 거래 내역
                    recent_trades = Transaction.query.order_by(
                        Transaction.timestamp.desc()
                    ).limit(10).all()
                    
                    # 대량 거래 내역 (1000주 이상)
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
                    # 다른 페이지의 경우 기존 데이터 전송
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

    @socketio.on('select_stock')
    def handle_select_stock(data):
        if not data:
            return
            
        stock_code = data.get('code')
        is_initial = data.get('initial', False)
        
        if not stock_code:
            return
            
        try:
            print(f'Stock selected: {stock_code}, initial: {is_initial}')
            with app.app_context():
                # 주식 기본 정보 가져오기
                stock = StockPrice.query.filter_by(code=stock_code).first()
                if stock:
                    try:
                        stock_data_dict = stock.to_dict()
                        
                        # 최초 선택 시에만 히스토리 데이터 전송
                        if is_initial:
                            history = PriceHistory.query.filter_by(code=stock_code)\
                                .order_by(PriceHistory.timestamp.desc())\
                                .limit(300)\
                                .all()
                            
                            if history:
                                # 시간순 정렬을 위해 리스트 뒤집기
                                history.reverse()
                                stock_data_dict['history'] = [h.to_dict() for h in history]
                                print(f'Sending history data: {len(stock_data_dict["history"])} records')
                        else:
                            # 최신 가격만 전송
                            latest_price = PriceHistory.query.filter_by(code=stock_code)\
                                .order_by(PriceHistory.timestamp.desc())\
                                .first()
                            if latest_price:
                                stock_data_dict['latest_price'] = latest_price.to_dict()
                                print(f'Sending latest price: {latest_price.price}')
                        
                        socketio.emit('stock_selected', stock_data_dict)
                    except Exception as process_error:
                        print(f"Error processing stock data: {str(process_error)}")
                        socketio.emit('error', {'message': '주식 데이터 처리 중 오류가 발생했습니다.'})
        except Exception as e:
            print(f"Error in handle_select_stock: {str(e)}")
            socketio.emit('error', {'message': '주식 선택 처리 중 오류가 발생했습니다.'})

    @socketio.on('trade')
    def handle_trade(data):
        try:
            with app.app_context():
                if not current_user or not current_user.is_authenticated:
                    socketio.emit('trade_error', {
                        'message': '로그인이 필요합니다.'
                    })
                    return

                stock_code = data.get('stock_code')
                quantity = int(data.get('quantity', 0))
                trade_type = data.get('type', '').upper()

                if not all([stock_code, quantity, trade_type]):
                    socketio.emit('trade_error', {
                        'message': '잘못된 요청입니다.'
                    }, room=f'user_{current_user.id}')
                    return

                stock = StockPrice.query.filter_by(code=stock_code).first()
                if not stock:
                    socketio.emit('trade_error', {
                        'message': '존재하지 않는 종목입니다.'
                    }, room=f'user_{current_user.id}')
                    return

                total_amount = stock.current_price * quantity

                if trade_type == 'BUY':
                    if current_user.cash < total_amount:
                        socketio.emit('trade_error', {
                            'message': '잔액이 부족합니다.'
                        }, room=f'user_{current_user.id}')
                        return

                    # 매수 처리
                    current_user.cash -= total_amount
                    current_user.buy_count += 1

                    # 보유 주식 업데이트
                    holding = StockHolding.query.filter_by(
                        user_id=current_user.id,
                        stock_code=stock_code
                    ).first()

                    if holding:
                        # 평균단가 계산
                        total_value = (holding.average_price * holding.quantity) + total_amount
                        holding.quantity += quantity
                        holding.average_price = total_value // holding.quantity
                    else:
                        holding = StockHolding(
                            user_id=current_user.id,
                            stock_code=stock_code,
                            stock_name=stock.name,
                            quantity=quantity,
                            average_price=stock.current_price
                        )
                        db.session.add(holding)

                elif trade_type == 'SELL':
                    holding = StockHolding.query.filter_by(
                        user_id=current_user.id,
                        stock_code=stock_code
                    ).first()

                    if not holding or holding.quantity < quantity:
                        socketio.emit('trade_error', {
                            'message': '보유 수량이 부족합니다.'
                        }, room=f'user_{current_user.id}')
                        return

                    # 매도 처리
                    current_user.cash += total_amount
                    current_user.sell_count += 1

                    # 보유 주식 업데이트
                    holding.quantity -= quantity
                    if holding.quantity == 0:
                        db.session.delete(holding)

                # 거래 기록 추가
                transaction = Transaction(
                    user_id=current_user.id,
                    stock_code=stock_code,
                    stock_name=stock.name,
                    transaction_type=trade_type,
                    quantity=quantity,
                    price=stock.current_price,
                    total_amount=total_amount
                )
                db.session.add(transaction)
                db.session.commit()

                # 거래 후 업데이트된 정보 전송
                holdings = get_user_holdings()
                total_assets = calculate_total_assets()
                invested_amount = calculate_invested_amount()
                
                # 거래 성공 알림
                socketio.emit('trade_success', {
                    'status': 'success',
                    'message': '거래가 완료되었습니다.',
                    'portfolio': {
                        'cash': current_user.cash,
                        'total_assets': total_assets,
                        'invested_amount': invested_amount,
                        'holdings': holdings
                    }
                }, room=f'user_{current_user.id}')

                # 거래 알림을 모든 클라이언트에게 전송
                trade_data = {
                    'type': trade_type.lower(),
                    'stock_name': stock.name,
                    'stock_code': stock_code,
                    'quantity': quantity,
                    'price': stock.current_price,
                    'timestamp': datetime.utcnow().isoformat()
                }
                socketio.emit('trade_update', {'trade': trade_data})

                # 모든 연결된 클라이언트에게 market_data 전송
                stocks = stock_data.get_all_stocks()
                total_users = User.query.count()
                
                socketio.emit('market_data', {
                    'stocks': stocks,
                    'total_users': total_users
                })

        except Exception as e:
            print(f"Error in handle_trade: {e}")
            db.session.rollback()
            try:
                if current_user and current_user.is_authenticated:
                    socketio.emit('trade_error', {
                        'message': '거래 처리 중 오류가 발생했습니다.'
                    }, room=f'user_{current_user.id}')
                else:
                    socketio.emit('trade_error', {
                        'message': '거래 처리 중 오류가 발생했습니다.'
                    })
            except Exception as emit_error:
                print(f"Error sending error message: {emit_error}")

    @socketio.on('request_leaderboard')
    def handle_leaderboard_request():
        """리더보드 데이터 요청 처리"""
        try:
            with app.app_context():
                users = User.query.all()
                total_users = len(users)
                leaderboard_data = []
                
                for user in users:
                    total_assets = user.cash
                    holdings = StockHolding.query.filter_by(user_id=user.id).all()
                    
                    for holding in holdings:
                        stock = StockPrice.query.filter_by(code=holding.stock_code).first()
                        if stock:
                            total_assets += stock.current_price * holding.quantity
                    
                    return_rate = ((total_assets - 10000000) / 10000000) * 100
                    
                    leaderboard_data.append({
                        'username': user.username,
                        'total_assets': total_assets,
                        'return_rate': return_rate
                    })
                
                # 총 자산 기준으로 내림차순 정렬
                leaderboard_data.sort(key=lambda x: x['total_assets'], reverse=True)
                
                # 순위 추가
                for i, data in enumerate(leaderboard_data):
                    data['rank'] = i + 1
                
                emit('market_data', {
                    'leaderboard': leaderboard_data,
                    'total_users': total_users
                })
                
        except Exception as e:
            print(f"Error in handle_leaderboard_request: {str(e)}")

    @socketio.on('message')
    def handle_message(data):
        """챗봇 메시지 처리"""
        try:
            with app.app_context():
                if not current_user.is_authenticated:
                    emit('error', {
                        'success': False,
                        'error': '로그인이 필요합니다.'
                    })
                    return
                    
                message = data.get('message', '')
                if not message:
                    emit('error', {
                        'success': False,
                        'error': '메시지가 비어있습니다.'
                    })
                    return
                    
                # 성격 변경 명령 처리
                if message.startswith('성격변경'):
                    try:
                        _, personality = message.split()
                        if personality in ['positive', 'negative', 'neutral']:
                            result = current_app.chatbot.set_personality(personality)
                            emit('bot_response', {
                                'success': True,
                                'response': result['message'],
                                'type': 'system',
                                'personality': result['personality']
                            })
                            return
                    except:
                        emit('error', {
                            'success': False,
                            'error': "올바른 식: '성격변경 [positive/negative/neutral]'"
                        })
                        return
                
                # 일반 메시지 처리
                result = current_app.chatbot.chat(message)
                emit('bot_response', {
                    'success': True,
                    'response': result['message'],
                    'type': 'assistant',
                    'personality': result['personality']
                })
                
        except Exception as e:
            print(f"Error in handle_message: {str(e)}")
            emit('error', {
                'success': False,
                'error': '메시지 처리 중 오류가 발생했습니다.'
            })

def get_user_holdings():
    """현재 사용자의 보유주식 정보를 가져옵니다."""
    if not current_user or not current_user.is_authenticated:
        return []
        
    try:
        holdings = StockHolding.query.filter_by(user_id=current_user.id).all()
        holdings_data = []
        
        for holding in holdings:
            # 현재가 조회
            stock = StockPrice.query.filter_by(code=holding.stock_code).first()
            if not stock:
                continue
                
            current_price = stock.current_price
            total_value = current_price * holding.quantity
            avg_price = holding.average_price
            profit_loss = total_value - (avg_price * holding.quantity)
            return_rate = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
            
            holdings_data.append({
                'stock_code': holding.stock_code,
                'stock_name': holding.stock_name,
                'quantity': holding.quantity,
                'avg_price': avg_price,
                'current_price': current_price,
                'total_value': total_value,
                'profit_loss': profit_loss,
                'return_rate': return_rate
            })
            
        return holdings_data
        
    except Exception as e:
        print(f"Error getting user holdings: {str(e)}")
        return []

def start_price_update_thread(socketio, stock_data, app):
    """가격 업데이트 스레드를 시작합니다."""
    global price_update_thread, stop_event
    
    if price_update_thread and price_update_thread.is_alive():
        return price_update_thread
    
    stop_event.clear()
    # stock_data의 price_update_thread 시작
    price_update_thread = stock_data.start_price_update_thread()
    return price_update_thread

def stop_price_update_thread():
    """가격 업데이트 스레드를 중지합니다."""
    global stop_event
    if stop_event:
        stop_event.set()

# 서버 종료 시 스레드 정리
atexit.register(stop_price_update_thread)

# 테스트를 위해 함수들 모듈 레벨로 노출
__all__ = ['handle_trade', 'init_socket_handlers', 'start_price_update_thread', 'stop_price_update_thread'] 

def calculate_total_assets():
    """사용자의 총 자산을 계산합니다."""
    if not current_user or not current_user.is_authenticated:
        return 0
        
    try:
        total = current_user.cash
        holdings = StockHolding.query.filter_by(user_id=current_user.id).all()
        
        for holding in holdings:
            stock = StockPrice.query.filter_by(code=holding.stock_code).first()
            if stock:
                total += stock.current_price * holding.quantity
                
        return total
        
    except Exception as e:
        print(f"Error calculating total assets: {str(e)}")
        return 0

def calculate_invested_amount():
    """사용자의 투자 금액을 계산합니다."""
    if not current_user or not current_user.is_authenticated:
        return 0
        
    try:
        total = 0
        holdings = StockHolding.query.filter_by(user_id=current_user.id).all()
        
        for holding in holdings:
            total += holding.average_price * holding.quantity
                
        return total
        
    except Exception as e:
        print(f"Error calculating invested amount: {str(e)}")
        return 0 