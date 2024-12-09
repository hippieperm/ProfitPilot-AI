from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, User, StockPrice
from werkzeug.security import generate_password_hash
import os

app = Flask(__name__)

# 설정
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///stock_game.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 데이터베이스 초기화
db.init_app(app)

# 마이그레이션 설정
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # 기존 데이터베이스 삭제
        db.drop_all()
        
        # 새 데이터베이스 생성
        db.create_all()
        
        # 테스트 사용자 생성
        # test_user = User(
        #     username='test',
        #     email='test@example.com',
        #     password_hash=generate_password_hash('test'),
        #     cash=10000000,
        #     buy_count=0,
        #     sell_count=0
        # )
        # db.session.add(test_user)
        
        # 초기 주식 데이터 생성
        initial_stocks = {
            '005930': {'code': '005930', 'name': '삼성전자', 'price': 72000, 'prev_price': 71500},
            '000660': {'code': '000660', 'name': 'SK하이닉스', 'price': 135000, 'prev_price': 134000},
            '035720': {'code': '035720', 'name': '카카오', 'price': 55000, 'prev_price': 54500},
            '035420': {'code': '035420', 'name': 'NAVER', 'price': 205000, 'prev_price': 204000},
            '005380': {'code': '005380', 'name': '현대차', 'price': 185000, 'prev_price': 184000},
            '051910': {'code': '051910', 'name': 'LG화학', 'price': 550000, 'prev_price': 548000},
            '006400': {'code': '006400', 'name': '삼성SDI', 'price': 750000, 'prev_price': 748000},
            '035900': {'code': '035900', 'name': 'JYP Ent.', 'price': 85000, 'prev_price': 84500},
            '352820': {'code': '352820', 'name': '하이브', 'price': 265000, 'prev_price': 264000},
            '003670': {'code': '003670', 'name': '포스코퓨처엠', 'price': 380000, 'prev_price': 378000},
            '207940': {'code': '207940', 'name': '삼성바이오로직스', 'price': 820000, 'prev_price': 818000},
            '373220': {'code': '373220', 'name': 'LG에너지솔루션', 'price': 450000, 'prev_price': 448000},
            '000270': {'code': '000270', 'name': '기아', 'price': 82000, 'prev_price': 81500},
            '068270': {'code': '068270', 'name': '셀트리온', 'price': 165000, 'prev_price': 164000},
            '105560': {'code': '105560', 'name': 'KB금융', 'price': 52000, 'prev_price': 51500},
            '055550': {'code': '055550', 'name': '신한지주', 'price': 36000, 'prev_price': 35800},
            '086790': {'code': '086790', 'name': '하나금융지주', 'price': 41000, 'prev_price': 40800},
            '316140': {'code': '316140', 'name': '우리금융지주', 'price': 12000, 'prev_price': 11900},
            '034730': {'code': '034730', 'name': 'SK', 'price': 155000, 'prev_price': 154000},
            '003550': {'code': '003550', 'name': 'LG', 'price': 82000, 'prev_price': 81500},
            '017670': {'code': '017670', 'name': 'SK텔레콤', 'price': 48000, 'prev_price': 47800},
            '030200': {'code': '030200', 'name': 'KT', 'price': 32000, 'prev_price': 31800},
            '032640': {'code': '032640', 'name': 'LG유플러스', 'price': 10000, 'prev_price': 9900},
            '015760': {'code': '015760', 'name': '한국전력', 'price': 19000, 'prev_price': 18900},
            '028260': {'code': '028260', 'name': '삼성물산', 'price': 110000, 'prev_price': 109000},
            '009150': {'code': '009150', 'name': '삼성전기', 'price': 150000, 'prev_price': 149000},
            '018260': {'code': '018260', 'name': '삼성에스디에스', 'price': 180000, 'prev_price': 179000},
            '036570': {'code': '036570', 'name': '엔씨소프트', 'price': 250000, 'prev_price': 249000},
            '251270': {'code': '251270', 'name': '넷마블', 'price': 48000, 'prev_price': 47800},
            '259960': {'code': '259960', 'name': '크래프톤', 'price': 180000, 'prev_price': 179000},
            '293490': {'code': '293490', 'name': '카카오게임즈', 'price': 25000, 'prev_price': 24800},
            '035760': {'code': '035760', 'name': 'CJ ENM', 'price': 70000, 'prev_price': 69500},
            '041510': {'code': '041510', 'name': 'SM', 'price': 120000, 'prev_price': 119000},
            '035600': {'code': '035600', 'name': 'KG이니시스', 'price': 12000, 'prev_price': 11900},
            '036530': {'code': '036530', 'name': '캠시스', 'price': 25000, 'prev_price': 24800},
            '067160': {'code': '067160', 'name': '아프리카TV', 'price': 75000, 'prev_price': 74500},
            '035720': {'code': '035720', 'name': '카카오', 'price': 55000, 'prev_price': 54500},
            '376300': {'code': '376300', 'name': '디어유', 'price': 28000, 'prev_price': 27800},
            '263750': {'code': '263750', 'name': '펄어비스', 'price': 35000, 'prev_price': 34800},
            '112040': {'code': '112040', 'name': '위메이드', 'price': 40000, 'prev_price': 39800}
        }
        
        for code, data in initial_stocks.items():
            stock = StockPrice(
                code=code,
                name=data['name'],
                current_price=data['price'],
                prev_price=data['prev_price']
            )
            db.session.add(stock)
        
        db.session.commit()
        print("Database initialized with initial stock data and test user")