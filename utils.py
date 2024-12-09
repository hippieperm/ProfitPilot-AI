import json
from functools import wraps
from flask import session, redirect, url_for
import os
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 데이터 디렉토리 생성
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 파일 경로 상수
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
PORTFOLIOS_FILE = os.path.join(DATA_DIR, 'portfolios.json')
STOCKS_FILE = os.path.join(DATA_DIR, 'stocks.json')
TRADES_FILE = os.path.join(DATA_DIR, 'trades.json')

def load_json(filename):
    """JSON 파일을 로드하는 유틸리티 함수"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {filename}, creating new file")
        data = {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {filename}")
        data = {}
    except Exception as e:
        logger.error(f"Unexpected error loading {filename}: {str(e)}")
        data = {}
    
    return data

def save_json(filename, data):
    """JSON 파일을 안전하게 저장하는 유틸리티 수"""
    try:
        # 임시 파일에 먼저 저장
        temp_file = f"{filename}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())

        # 파일 교체
        if os.path.exists(filename):
            os.replace(filename, f"{filename}.bak")
        os.replace(temp_file, filename)
        return True

    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def get_current_user():
    """현재 로그인한 사용자 정보를 반환"""
    if 'user_id' not in session:
        return None
    
    users = load_json(USERS_FILE)
    user_id = str(session['user_id'])
    if user_id in users:
        return {'id': user_id, **users[user_id]}
    return None

def get_user_portfolio(user_id):
    """사용자의 포트폴리오 정보를 반환"""
    portfolios = load_json(PORTFOLIOS_FILE)
    user_id = str(user_id)
    
    if user_id not in portfolios:
        # 포트폴리오가 없는 경우 기본값 생성
        portfolios[user_id] = {
            'user_id': user_id,
            'balance': 10000000,
            'total_value': 10000000,
            'total_return': 0,
            'trade_count': 0,
            'stocks': {},
            'trade_history': []
        }
        save_json(PORTFOLIOS_FILE, portfolios)
    
    portfolio = portfolios[user_id]
    
    # 보유 주식 정보 업데이트
    stocks = get_all_stocks()
    total_stock_value = 0
    
    for stock_id, holding in portfolio['stocks'].items():
        if stock_id in stocks:
            current_price = stocks[stock_id]['price']
            current_value = current_price * holding['quantity']
            total_stock_value += current_value
            
            holding.update({
                'current_price': current_price,
                'current_value': current_value,
                'profit': current_value - (holding['avg_price'] * holding['quantity']),
                'profit_percent': ((current_price - holding['avg_price']) / holding['avg_price'] * 100)
            })
    
    # 총 자산 및 수익률 업데이트
    portfolio['total_value'] = portfolio['balance'] + total_stock_value
    portfolio['total_return'] = ((portfolio['total_value'] - 10000000) / 10000000) * 100
    
    save_json(PORTFOLIOS_FILE, portfolios)
    return portfolio

def get_all_stocks():
    """모든 주식 데이터 가져오기"""
    try:
        stocks = load_json(STOCKS_FILE)
        if not stocks:
            # 기본 주식 데이터 생성
            stocks = {
                'SAMSUNG': {
                    'id': 'SAMSUNG',
                    'symbol': 'SAMSUNG',
                    'name': '삼성전자',
                    'price': 70000,
                    'change': 0.0
                },
                'SK': {
                    'id': 'SK',
                    'symbol': 'SK',
                    'name': 'SK하이닉스',
                    'price': 120000,
                    'change': 0.0
                },
                'NAVER': {
                    'id': 'NAVER',
                    'symbol': 'NAVER',
                    'name': '네이버',
                    'price': 200000,
                    'change': 0.0
                },
                'KAKAO': {
                    'id': 'KAKAO',
                    'symbol': 'KAKAO',
                    'name': '카카오',
                    'price': 55000,
                    'change': 0.0
                },
                'LG': {
                    'id': 'LG',
                    'symbol': 'LG',
                    'name': 'LG전자',
                    'price': 95000,
                    'change': 0.0
                }
            }
            save_json(STOCKS_FILE, stocks)
        return stocks
    except Exception as e:
        logger.error(f"Error loading stocks: {str(e)}")
        return {}

def get_leaderboard(limit=5):
    """리더보드 데이터를 반환"""
    portfolios = load_json(PORTFOLIOS_FILE)
    users = load_json(USERS_FILE)
    
    # 포트폴리오 정렬
    sorted_portfolios = sorted(
        [{'user_id': user_id, **portfolio} 
         for user_id, portfolio in portfolios.items()],
        key=lambda x: float(x.get('total_value', 0)),
        reverse=True
    )[:limit]
    
    # 리더보드 생성
    leaderboard = []
    for rank, portfolio in enumerate(sorted_portfolios, 1):
        user_id = portfolio['user_id']
        if user_id in users:
            leaderboard.append({
                'rank': rank,
                'username': users[user_id]['username'],
                'total_value': portfolio['total_value'],
                'total_return': portfolio.get('total_return', 0)
            })
    
    return leaderboard

def calculate_market_value():
    """전체 시장 가치 계산"""
    portfolios = load_json(PORTFOLIOS_FILE)
    return sum(float(p.get('total_value', 0)) for p in portfolios.values())

def get_user_count():
    """전체 사용자 수 계산"""
    users = load_json(USERS_FILE)
    return len(users)

def get_trade_volume():
    """전체 거래량 계산"""
    trades = load_json(TRADES_FILE)
    return len(trades)

def login_required(f):
    """로그인이 필요한 페이지에 대한 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_all_users():
    """모든 사용자 정보를 반환"""
    users = load_json(USERS_FILE)
    return [{'id': user_id, **user_data} for user_id, user_data in users.items()]

def save_trade_history(user_id, stock_id, trade_type, quantity, price):
    """거래 내역 저장"""
    try:
        trades = load_json(TRADES_FILE)
        if 'trades' not in trades:
            trades['trades'] = []
            
        trade = {
            'user_id': str(user_id),
            'stock_id': str(stock_id),
            'type': trade_type,
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.now().timestamp()
        }
        
        trades['trades'].append(trade)
        save_json(TRADES_FILE, trades)
        return True
    except Exception as e:
        logger.error(f"Error saving trade history: {str(e)}")
        return False