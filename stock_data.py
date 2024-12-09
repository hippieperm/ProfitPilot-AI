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
    
    def get_stock(self, code):
        if not self.app:
            return None
            
        with self.app.app_context():
            stock = StockPrice.query.filter_by(code=code).first()
            if stock:
                current_price = stock.current_price
                prev_price = self.current_prices.get(code, current_price)
                price_diff = current_price - prev_price
                change_rate = (price_diff / prev_price * 100) if prev_price > 0 else 0
                
                return {
                    'code': stock.code,
                    'name': stock.name,
                    'price': current_price,
                    'price_diff': price_diff,
                    'change_rate': change_rate
                }
        return None
    
    def get_all_stocks(self):
        if not self.app:
            return []
            
        with self.app.app_context():
            stocks = StockPrice.query.all()
            result = []
            for stock in stocks:
                current_price = stock.current_price
                prev_price = self.current_prices.get(stock.code, current_price)
                price_diff = current_price - prev_price
                change_rate = (price_diff / prev_price * 100) if prev_price > 0 else 0
                
                result.append({
                    'code': stock.code,
                    'name': stock.name,
                    'current_price': current_price,
                    'price_diff': price_diff,
                    'change_rate': change_rate
                })
            return result
    
    def get_price_history(self, code, limit=stockHistoryLimit):
        """특정 주식의 가격 히스토리를 가져옵니다."""
        if not self.app:
            return []
            
        with self.app.app_context():
            history = PriceHistory.query.filter_by(code=code)\
                .order_by(PriceHistory.timestamp.desc())\
                .limit(limit)\
                .all()
            
            # 시간순으로 정렬하여 반환
            return sorted([h.to_dict() for h in history], key=lambda x: x['timestamp'])
    
    def start_price_update_thread(self):
        """가격 업데이트 스레드를 시작합니다."""
        def update_prices():
            print("Price update thread started")
            last_update = {}  # 마지막 업데이트 시간 저장
            
            while not self._stop_event.is_set():
                try:
                    current_time = time.time()
                    with self.app.app_context():
                        # 모든 주식의 가격 업데이트
                        stocks = StockPrice.query.all()
                        updated_stocks = []
                        significant_changes = False  # 유의미한 변화 감지
                        
                        for stock in stocks:
                            # 새로운 가격 계산 및 저장
                            new_price = self.calculate_new_price(stock)
                            
                            # 가격 변화가 0.1% 이상인 경우에만 업데이트
                            price_change_rate = abs(new_price - stock.current_price) / stock.current_price * 100
                            if price_change_rate >= 0.1:  # 0.1% 이상 변화가 있을 때만 업데이트
                                significant_changes = True
                                stock.current_price = new_price
                                # prev_price는 변경하지 않음
                                
                                # 가격 히스토리 저장
                                if stock.code not in last_update or (current_time - last_update[stock.code]) >= stockUpdateInterval:
                                    history = PriceHistory(
                                        code=stock.code,
                                        price=new_price
                                    )
                                    db.session.add(history)
                                    last_update[stock.code] = current_time
                                    
                                    # 오래된 히스토리 삭제 (24시간 이전 데이터)
                                    PriceHistory.query.filter(
                                        PriceHistory.code == stock.code,
                                        PriceHistory.timestamp < datetime.utcnow() - timedelta(hours=24)
                                    ).delete()
                            
                            # to_dict() 메서드를 통해 등락률 계산 (prev_price 기준)
                            updated_stocks.append(stock.to_dict())
                        
                        if significant_changes:
                            db.session.commit()
                            
                            # 변화가 있을 때만다 리더보드 데이터도 함께 업데이트
                            users = User.query.all()
                            total_users = len(users)
                            leaderboard_data = []
                            
                            for user in users:
                                total_assets = user.cash
                                holdings = StockHolding.query.filter_by(user_id=user.id).all()
                                
                                # 각 사용자의 포트폴리오 정보 계산
                                user_holdings = []
                                invested_amount = 0
                                
                                for holding in holdings:
                                    stock = StockPrice.query.filter_by(code=holding.stock_code).first()
                                    if stock:
                                        current_value = stock.current_price * holding.quantity
                                        total_assets += current_value
                                        
                                        user_holdings.append({
                                            'stock_name': holding.stock_name,
                                            'stock_code': holding.stock_code,
                                            'quantity': holding.quantity,
                                            'avg_price': holding.average_price,
                                            'current_price': stock.current_price,
                                            'total_value': current_value,
                                            'profit_loss': current_value - (holding.average_price * holding.quantity),
                                            'return_rate': ((stock.current_price / holding.average_price) - 1) * 100 if holding.average_price > 0 else 0
                                        })
                                
                                # 리더보드 데이터 추가
                                leaderboard_data.append({
                                    'username': user.username,
                                    'total_assets': total_assets,
                                    'return_rate': ((total_assets - 10000000) / 10000000) * 100
                                })
                                
                                # 개별 사용자에게 포트폴리오 업데이트 전송
                                if self.socketio:
                                    self.socketio.emit('market_data', {
                                        'holdings': user_holdings,
                                        'total_assets': total_assets,
                                        'invested_amount': invested_amount,
                                        'cash': user.cash
                                    }, room=f'user_{user.id}')
                            
                            # 리더보드 정렬 및 순위 추가
                            leaderboard_data.sort(key=lambda x: x['total_assets'], reverse=True)
                            for i, data in enumerate(leaderboard_data):
                                data['rank'] = i + 1
                            
                            # 모든 클라이언트에게 업데이트된 데이터 전송
                            if self.socketio:
                                self.socketio.emit('market_data', {
                                    'stocks': updated_stocks,
                                    'leaderboard': leaderboard_data,
                                    'total_users': total_users
                                })
                
                except Exception as e:
                    print(f"Error in price update thread: {e}")
                    if 'db' in locals():
                        db.session.rollback()
                
                time.sleep(stockUpdateInterval)
        
        if not self._update_thread or not self._update_thread.is_alive():
            self._stop_event.clear()
            self._update_thread = Thread(target=update_prices)
            self._update_thread.daemon = True
            self._update_thread.start()
        
        return self._update_thread
        
    def update_user_holdings(self):
        """사용자들의 보유 주식 정보를 업데이트합니다."""
        try:
            users = User.query.all()
            
            for user in users:
                holdings = []
                total_assets = user.cash
                invested_amount = 0
                
                user_stocks = StockHolding.query.filter_by(user_id=user.id).all()
                for user_stock in user_stocks:
                    stock = StockPrice.query.filter_by(code=user_stock.stock_code).first()
                    if stock:
                        current_price = stock.current_price
                        total_value = current_price * user_stock.quantity
                        profit_loss = total_value - (user_stock.average_price * user_stock.quantity)
                        return_rate = ((current_price / user_stock.average_price) - 1) * 100
                        invested_amount += user_stock.average_price * user_stock.quantity
                        
                        holdings.append({
                            'stock_name': user_stock.stock_name,
                            'stock_code': user_stock.stock_code,
                            'quantity': user_stock.quantity,
                            'avg_price': user_stock.average_price,
                            'current_price': current_price,
                            'total_value': total_value,
                            'profit_loss': profit_loss,
                            'return_rate': return_rate
                        })
                        
                        total_assets += total_value

                # 개별 사용자에게 포트폴리오 데이터만 전송
                if self.socketio:
                    self.socketio.emit('market_data', {
                        'holdings': holdings,
                        'total_assets': total_assets,
                        'invested_amount': invested_amount,
                        'cash': user.cash
                    }, room=f'user_{user.id}')

        except Exception as e:
            print(f"Error updating user holdings: {str(e)}")
            if 'db' in locals():
                db.session.rollback()
    
    def calculate_new_price(self, stock):
        """새로운 가격을 계산하고 반환합니다."""
        prev_price = stock.current_price
        
        # 변동폭 설정 (기본 -0.5% ~ +0.5%)
        base_volatility = 0.005
        
        # 시가총액이 큰 종목은 변동성이 작게
        if prev_price * 100000 > 100000000000:  # 시가총액 1000억 이상
            volatility = base_volatility * 0.7  # 대형주는 변동성 30% 감소
        else:
            volatility = base_volatility * 1.2  # 중소형주는 변동성 20% 증가
        
        # 랜덤 요소 추가 (가끔 큰 변동 발생)
        if random.random() < 0.1:  # 10% 확률로
            volatility *= 2  # 변동성 2배
        
        # 추세 반영 (이전 변동 향을 일부 반영)
        trend = 0
        if hasattr(stock, 'last_change'):
            trend = stock.last_change * 0.3  # 30% 반영
        
        # 최종 변동폭 계산
        price_change = random.uniform(-volatility, volatility) * prev_price
        price_change += trend
        
        # 새 가격 계산
        new_price = prev_price + int(price_change)
        
        # 1의 자리 숫자 랜덤 조정 (±9 범위)
        #ones_digit_change = random.randint(-9, 9)
        new_price #+= ones_digit_change
        
        return new_price
    
    def stop_price_updates(self):
        """가격 업데이트를 중지하고 현재 가격을 저장"""
        self._stop_event.set()
        if self._update_thread:
            self._update_thread.join(timeout=5)
            # 스레드 종료 전 현재 가격 저장
            self.save_current_prices()
            print("Price update thread stopped and prices saved")

# 전역 인스턴스 생성
stock_data = StockData()