from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(120), nullable=False)
    cash = db.Column(db.Integer, default=10000000)  # 초기 자금 1000만원
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    buy_count = db.Column(db.Integer, default=0)  # 매수 횟수
    sell_count = db.Column(db.Integer, default=0)  # 매도 횟수
    
    # 관계 설정
    holdings = db.relationship('StockHolding', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'cash': self.cash,
            'total_assets': self.get_total_assets(),
            'buy_count': self.buy_count,
            'sell_count': self.sell_count
        }
    
    def get_total_assets(self):
        total = self.cash
        for holding in self.holdings:
            total += holding.current_value
        return total
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class StockPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    current_price = db.Column(db.Integer, nullable=False)
    prev_price = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'code': self.code,
            'name': self.name,
            'price': self.current_price,
            'prev_price': self.prev_price,
            'price_diff': self.current_price - self.prev_price,
            'change_rate': ((self.current_price - self.prev_price) / self.prev_price) * 100
        }

class StockHolding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_code = db.Column(db.String(20), nullable=False)
    stock_name = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    average_price = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def current_value(self):
        stock_price = StockPrice.query.filter_by(code=self.stock_code).first()
        if stock_price:
            return stock_price.current_price * self.quantity
        return 0
    
    def to_dict(self):
        stock_price = StockPrice.query.filter_by(code=self.stock_code).first()
        current_price = stock_price.current_price if stock_price else 0
        current_value = self.current_value
        profit_loss = current_value - (self.average_price * self.quantity)
        return_rate = ((current_price / self.average_price) - 1) * 100 if self.average_price > 0 else 0
        
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'quantity': self.quantity,
            'avg_price': self.average_price,
            'current_price': current_price,
            'total_value': current_value,
            'profit_loss': profit_loss,
            'return_rate': return_rate
        }

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_code = db.Column(db.String(20), nullable=False)
    stock_name = db.Column(db.String(50), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'BUY' or 'SELL'
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'transaction_type': '매수' if self.transaction_type == 'BUY' else '매도',
            'quantity': self.quantity,
            'price': self.price,
            'total_amount': self.total_amount,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_code_timestamp', 'code', 'timestamp'),
    )

    def to_dict(self):
        return {
            'price': self.price,
            'timestamp': self.timestamp.strftime('%H:%M:%S')
        }