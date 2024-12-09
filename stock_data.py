import random
import time
from threading import Thread, Event
from datetime import datetime, timedelta
from models import db, StockPrice, PriceHistory, User, StockHolding

stockUpdateInterval = 0.05 # 주식 가격 업데이트 주기
stockHistoryLimit = 200 # 주식 가격 히스토리 불러오기 개수

class StockData:
    _instance = None
    _initialized = False
    _update_thread = None
    _stop_event = Event()
    _selected_stock = None  # 선택된 주식 코드를 클래스 변수로 관리
    
    def __new__(cls, socketio=None):
        if cls._instance is None:
            cls._instance = super(StockData, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, socketio=None, app=None):
        if self._initialized:
            if socketio:
                self.socketio = socketio
            if app:
                self.app = app
            return
        
        self._initialized = True
        self.socketio = socketio
        self.app = app
        
        # 초기 주식 데이터
        self.initial_stocks = {
            '005930': {'code': '005930', 'name': '삼성전자', 'price': 72000},
            '000660': {'code': '000660', 'name': 'SK하이닉스', 'price': 135000},
            '035720': {'code': '035720', 'name': '카카오', 'price': 55000},
            '035420': {'code': '035420', 'name': 'NAVER', 'price': 205000},
            '005380': {'code': '005380', 'name': '현대차', 'price': 185000},
            '051910': {'code': '051910', 'name': 'LG화학', 'price': 550000},
            '006400': {'code': '006400', 'name': '삼성SDI', 'price': 750000},
            '035900': {'code': '035900', 'name': 'JYP Ent.', 'price': 85000},
            '352820': {'code': '352820', 'name': '하이브', 'price': 265000},
            '003670': {'code': '003670', 'name': '포스코퓨처엠', 'price': 380000}
        }
        
        # 현재 가격 저장용 딕셔너리
        self.current_prices = {}
    
    @classmethod
    def set_selected_stock(cls, code):
        """선택된 주식 코드를 설정합니다."""
        cls._selected_stock = code

    @classmethod
    def get_selected_stock(cls):
        """선택된 주식 코드를 반환합니다."""
        return cls._selected_stock
    
    def initialize_db(self):
        """데이터베이스에 초기 주식 데이터 설정"""
        if not self.app:
            print("App context not available")
            return
            
        try:
            with self.app.app_context():
                # 기존 주식 데이터 확인
                for code, data in self.initial_stocks.items():
                    stock = StockPrice.query.filter_by(code=code).first()
                    if not stock:
                        # 새로운 주식 데이터 추가
                        stock = StockPrice(
                            code=code,
                            name=data['name'],
                            current_price=data['price'],
                            prev_price=data['price']
                        )
                        db.session.add(stock)
                        self.current_prices[code] = data['price']
                    else:
                        # 하루가 지났거나 prev_price가 없는 경우에만 prev_price 업데이트
                        now = datetime.utcnow()
                        if (now - stock.updated_at).days >= 1:
                            stock.prev_price = stock.current_price
                            self.current_prices[code] = stock.current_price
                
                db.session.commit()
                print("Stock data initialized in database")
        except Exception as e:
            print(f"Error initializing stock data: {e}")
            if 'db' in locals():
                db.session.rollback()
    
    def save_current_prices(self):
        """현재 가격을 데이터베이스에 저장"""
        if not self.app:
            return
            
        try:
            with self.app.app_context():
                for code, price in self.current_prices.items():
                    stock = StockPrice.query.filter_by(code=code).first()
                    if stock:
                        stock.prev_price = stock.current_price
                        stock.current_price = price
                db.session.commit()
                print("Current prices saved to database")
        except Exception as e:
            print(f"Error saving current prices: {e}")
            if 'db' in locals():
                db.session.rollback()
