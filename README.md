• 프로젝트 명: ProfitPilot AI 프로젝트

• 회의 주기: 매주 금요일

• 참여 인원: 김태희, 김서현, 송주영, 이인혁

• 프로젝트 시작일: 9월 20일

![image](https://github.com/user-attachments/assets/8a0cf539-358e-4cae-8c4e-6854e85f61a7)



![KakaoTalk_Photo_2024-12-09-18-08-46](https://github.com/user-attachments/assets/ace375b0-56f2-45d7-a14f-32a3203d62dc)


# 주식 거래 시뮬레이션 프로젝트

실시간 주식 거래를 시뮬레이션하는 웹 애플리케이션입니다. Flask 기반의 백엔드와 WebSocket을 통한 실시간 데이터 처리를 제공합니다.

## 관리 및 사용법

### 1. 서버 관리

#### 데이터베이스 관리
```bash
# 데이터베이스 초기화
flask db init

# 마이그레이션 생성
flask db migrate -m "migration message"

# 마이그레이션 적용
flask db upgrade

# 마이그레이션 롤백
flask db downgrade
```

#### 사용자 관리
```bash
# 주식 목록 업데이트 및 초기화
python manage.py 

```

### 2. 환경 설정

#### 개발 환경 설정 (.env)
```bash
config.py 파일 참고
```

### 3. 주식 설정 변경

#### 변동성 설정 (stock_data.py)
```python
# 대형주 변동성 (기본: 0.7)
LARGE_CAP_VOLATILITY = 0.7

# 중소형주 변동성 (기본: 1.2)
SMALL_CAP_VOLATILITY = 1.2

# 급격한 변동 확률 (기본: 0.1)
SUDDEN_CHANGE_PROBABILITY = 0.1
```

#### 거래 제한 설정 (config.py)
```python
# 최소 거래 수량
MIN_TRADE_QUANTITY = 1

# 최대 거래 수량
MAX_TRADE_QUANTITY = 100000

# 거래 수수료율
TRADE_FEE_RATE = 0.0015  # 0.15%
```


## 핵심 기능 설명

### 1. 실시간 가격 업데이트 (stock_data.py)
- 주식 가격 자동 업데이트 시스템
- 개별 주식별 변동성 조절
  ```python
  # 대형주/중소형주 변동성 차등 적용
  if prev_price * 100000 > 100000000000:  # 시가총액 1000억 이상
      volatility = base_volatility * 0.7  # 대형주는 변동성 30% 감소
  else:
      volatility = base_volatility * 1.2  # 중소형주는 변동성 20% 증가
  ```

### 2. 실시간 데이터 통신 (socket_handlers.py)
- WebSocket을 통한 양방향 실시간 통신
- 주요 이벤트 핸들러:
  ```python
  # 주식 선택 시 히스토리 데이터 전송
  @socketio.on('select_stock')
  def handle_select_stock(data):
      history = PriceHistory.query.filter_by(code=stock_code)\
          .order_by(PriceHistory.timestamp.desc())\
          .limit(300)\
          .all()
  ```

### 3. 차트 시스템 (static/js/market.js)
- Chart.js를 활용한 실시간 차트
- 가격 데이터 실시간 업데이트
  ```javascript
  appendPriceToChart: function(priceData) {
      if (this.priceChart.data.labels.length > 100) {
          this.priceChart.data.labels.shift();
          this.priceChart.data.datasets[0].data.shift();
      }
      this.priceChart.data.labels.push(timeString);
      this.priceChart.data.datasets[0].data.push(parseFloat(priceData.price));
  }
  ```

### 4. 거래 시스템 (socket_handlers.py)
- 실시간 매수/매도 처리
- 잔고 및 포트폴리오 자동 업데이트
  ```python
  @socketio.on('trade')
  def handle_trade(data):
      # 매수 처리
      if trade_type == 'BUY':
          current_user.cash -= total_amount
          holding.quantity += quantity
          holding.average_price = total_value // holding.quantity
      
      # 매도 처리
      elif trade_type == 'SELL':
          current_user.cash += total_amount
          holding.quantity -= quantity
  ```

### 5. 포트폴리오 관리 (models.py)
- 실시간 자산 가치 계산
- 수익률 및 손익 추적
  ```python
  class StockHolding(db.Model):
      user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
      stock_code = db.Column(db.String(20))
      quantity = db.Column(db.Integer)
      average_price = db.Column(db.Integer)
  ```

## 주요 설정 파라미터

### 가격 변동 설정 (stock_data.py)
```python
stockUpdateInterval = 1  # 가격 업데이트 주기 (초)
base_volatility = 0.005  # 기본 변동성 (0.5%)
price_change_threshold = 0.1  # 가격 변동 임계값 (0.1%)
```

### 차트 설정 (static/js/market.js)
```javascript
// 차트 데이터 포인트 제한
if (this.priceChart.data.labels.length > 100) {
    this.priceChart.data.labels.shift();
}

// Y축 범위 자동 조정
const padding = (maxPrice - minPrice) * 0.1;
this.priceChart.options.scales.y.min = Math.floor(minPrice - padding);
this.priceChart.options.scales.y.max = Math.ceil(maxPrice + padding);
```

## 프로젝트 구조 설명

### 백엔드 (Python/Flask)
- `app.py`: 애플리케이션 초기화 및 설정
- `socket_handlers.py`: WebSocket 이벤트 처리
- `stock_data.py`: 주식 가격 시뮬레이션 로직
- `models.py`: 데이터베이스 모델 정의

### 프론트엔드 (JavaScript)
- `static/js/market.js`: 거래소 페이지 로직
- `static/js/portfolio.js`: 포트폴리오 관리
- `static/js/socket.js`: WebSocket 연결 관리

### 데이터베이스 모델
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cash = db.Column(db.Integer, default=10000000)
    holdings = db.relationship('StockHolding', backref='user')

class StockPrice(db.Model):
    code = db.Column(db.String(20), primary_key=True)
    current_price = db.Column(db.Integer)
    prev_price = db.Column(db.Integer)
```

## 실시간 데이터 흐름

1. 가격 업데이트:
   ```
   stock_data.py (가격 계산) 
   → socket_handlers.py (이벤트 발생) 
   → market.js (차트 업데이트)
   ```

2. 거래 처리:
   ```
   market.js (거래 요청) 
   → socket_handlers.py (거래 처리) 
   → models.py (DB 업데이트) 
   → market.js (UI 업데이트)
   ```
