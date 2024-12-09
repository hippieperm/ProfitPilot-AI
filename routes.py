from chatbot import PersonalityBot
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user, login_user, logout_user
from models import db, User, StockHolding, Transaction, StockPrice
from stock_data import stock_data
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm
from urllib.parse import urlparse, urljoin
import logging
from logging.handlers import RotatingFileHandler
import os
import traceback
from datetime import datetime


# 전역 변수로 챗봇 인스턴스 생성하는 부분 제거
# chatbot = PersonalityBot()  # 이 줄 삭제

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)

# 로깅 설정 함수 추가
def setup_logging(app):
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler(
        'logs/stock_game.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Stock Game startup')

# Blueprint 정의 후에 에러 핸들러 추가
@main.errorhandler(Exception)
def handle_error(error):
    error_message = f"예기치 않은 오류가 발생했습니다: {str(error)}"
    stack_trace = traceback.format_exc()
    
    # 에러 로깅
    current_app.logger.error(f'{error_message}\n{stack_trace}')
    
    # API 요청인 경우 JSON 응답
    if request.path.startswith('/api/'):
        return jsonify({
            'error': error_message,
            'status': 'error'
        }), 500
    
    # 일반 웹 요청인 경우 에러 페이지 렌더링
    return render_template('error.html', error=error_message), 500

# 포트폴리오 계산 헬퍼 함수
def calculate_portfolio_data(user):
    """사용자의 포트폴리오 정보를 계산합니다."""
    try:
        holdings = StockHolding.query.filter_by(user_id=user.id).all()
        total_assets = user.cash if user.cash is not None else 0
        invested_amount = 0
        holdings_data = []

        for holding in holdings:
            try:
                holding_dict = holding.to_dict()
                total_value = holding_dict['total_value']
                avg_price = holding_dict['avg_price']
                quantity = holding_dict['quantity']

                holdings_data.append({
                    'stock_name': holding_dict['stock_name'],
                    'quantity': quantity,
                    'avg_price': avg_price,
                    'current_price': holding_dict['current_price'],
                    'total_value': total_value,
                    'return_rate': holding_dict['return_rate'],
                    'profit_loss': holding_dict['profit_loss']
                })

                total_assets += total_value
                invested_amount += avg_price * quantity
            except Exception as e:
                print(f"Error processing holding {holding.id}: {str(e)}")
                continue

        # 총 수익 계산
        total_return_rate = ((total_assets - 10000000) / 10000000) * 100 if total_assets > 0 else 0

        return {
            'holdings': holdings_data,
            'total_assets': total_assets,
            'invested_amount': invested_amount,
            'total_return_rate': total_return_rate,
            'cash': user.cash
        }
    except Exception as e:
        current_app.logger.error(f"포트폴리오 데이터 계산 중 오류 발생 (User ID: {user.id}): {str(e)}\n{traceback.format_exc()}")
        return {
            'holdings': [],
            'total_assets': user.cash if user.cash is not None else 0,
            'invested_amount': 0,
            'total_return_rate': 0,
            'cash': user.cash if user.cash is not None else 0
        }

@main.route('/')
def index():
    """홈페이지를 표시합니다."""
    try:
        # 기본 데이터 준비
        context = {
            'stocks': [],
            'portfolio': None
        }
        
        # 주식 데이터 가져오기 시도
        try:
            context['stocks'] = stock_data.get_all_stocks() if stock_data else []
        except Exception as stock_error:
            print(f"Error getting stock data: {str(stock_error)}")
        
        # 로그인한 사용자의 경우 트폴리오 데이터 가져오기 시도
        if current_user and current_user.is_authenticated:
            try:
                context['portfolio'] = calculate_portfolio_data(current_user)
            except Exception as portfolio_error:
                print(f"Error getting portfolio data: {str(portfolio_error)}")
        
        return render_template('home.html', **context)
        
    except Exception as e:
        print(f"Critical error in index route: {str(e)}")
        # 최소한의 컨텍스트로 기본 페이지 렌더링 시도
        return render_template('home.html', stocks=[], portfolio=None)

@main.route('/market')
@login_required
def market():
    current_app.logger.info("Market route accessed")
    try:
        # 주식 데이터 가져오기
        try:
            current_app.logger.info("Fetching stock data...")
            stocks = stock_data.get_all_stocks()
            current_app.logger.info(f"Fetched {len(stocks)} stocks")
            
            if not stocks:
                current_app.logger.error("No stock data available")
                flash('주식 데이터를 불러올 수 없습니다.', 'error')
                return redirect(url_for('main.index'))
                
            # 주식 데이터 로깅
            for stock in stocks:
                current_app.logger.debug(f"Stock: {stock}")
                
        except Exception as stock_error:
            current_app.logger.error(f"Error fetching stock data: {str(stock_error)}\n{traceback.format_exc()}")
            flash('주식 데이터를 불러올 수 없습니다.', 'error')
            return redirect(url_for('main.index'))

        # 포트폴리오 데이터 가져오기
        try:
            current_app.logger.info("Fetching portfolio data...")
            portfolio_data = calculate_portfolio_data(current_user)
            current_app.logger.info(f"Portfolio data: {portfolio_data}")
            
            if not portfolio_data:
                current_app.logger.warning("No portfolio data available")
                portfolio_data = {
                    'holdings': [],
                    'cash': current_user.cash if current_user.cash is not None else 0
                }
        except Exception as portfolio_error:
            current_app.logger.error(f"Error fetching portfolio data: {str(portfolio_error)}\n{traceback.format_exc()}")
            portfolio_data = {
                'holdings': [],
                'cash': current_user.cash if current_user.cash is not None else 0
            }

        # 템플릿 렌더링
        current_app.logger.info("Rendering market template...")
        return render_template('market.html', 
            stocks=stocks, 
            holdings=portfolio_data.get('holdings', [])
        )

    except Exception as e:
        current_app.logger.error(f"Error in market route: {str(e)}\n{traceback.format_exc()}")
        flash('거래소 정보를 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('main.index'))

@main.route('/portfolio')
@login_required
def portfolio():
    try:
        portfolio_data = calculate_portfolio_data(current_user)
        transactions = Transaction.query.filter_by(user_id=current_user.id)\
            .order_by(Transaction.timestamp.desc())\
            .limit(10)\
            .all()
        
        return render_template('portfolio.html',
            holdings=portfolio_data['holdings'],
            transactions=transactions,
            cash=portfolio_data['cash'],
            total_assets=portfolio_data['total_assets'],
            invested_amount=portfolio_data['invested_amount'],
            total_return_rate=portfolio_data['total_return_rate']
        )
    except Exception as e:
        print(f"Error in portfolio page: {str(e)}")
        flash('포트폴리오 정보를 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('main.index'))

@main.route('/transactions')
@login_required
def transactions():
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.timestamp.desc())\
        .all()
    
    # 총 거래금 계산
    total_amount = sum(tx.total_amount for tx in transactions)
    
    return render_template('transactions.html', 
        transactions=transactions,
        total_amount=total_amount
    )

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember.data)
                flash('로그인되었습니다.', 'success')
                
                next_page = request.args.get('next')
                if not next_page or not is_safe_url(next_page):
                    next_page = url_for('main.index')
                
                return redirect(next_page)
            else:
                flash('잘못된 사용자 이름 또는 비밀번호입니다.', 'error')
        except Exception as e:
            print(f"Error in login: {str(e)}")
            flash('로그인 처리 중 오류가 발생했습니다.', 'error')
    
    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    try:
        form = RegistrationForm()
        if form.validate_on_submit():
            current_app.logger.info(f'회원가입 시도: {form.username.data}')
            
            # 사용자 중복 확인
            if User.query.filter_by(username=form.username.data).first():
                current_app.logger.warning(f'회원가입 실패: 중복된 사용자 이름 - {form.username.data}')
                flash('이미 사용 중인 사용자 이름입니다.', 'error')
                return redirect(url_for('auth.register'))
            
            # 이메일 중복 확인
            if User.query.filter_by(email=form.email.data).first():
                current_app.logger.warning(f'회원가입 실패: 중복된 이메일 - {form.email.data}')
                flash('이미 사용 중인 이메일입니다.', 'error')
                return redirect(url_for('auth.register'))
            
            try:
                # 새 사용자 생성
                user = User(
                    username=form.username.data,
                    email=form.email.data,
                    cash=10000000  # 초기 자본금 설정
                )
                user.set_password(form.password.data)
                
                # 데이터베이스에 사용자 추가
                db.session.add(user)
                db.session.commit()
                
                # 회원가입 성공 로그
                current_app.logger.info(f'회원가입 성공: {user.username}')
                
                # 자동 로그인 처리
                login_user(user)
                
                # 성공 메시지 표시
                flash(f'회원가입이 완료되었습니다. {user.username}님 환영합니다!', 'success')
                
                return redirect(url_for('main.index'))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'회원가입 처리 중 오류 발생: {str(e)}')
                flash('회원가입 처리 중 오류가 발생했습니다. 다시 시도해 주세요.', 'error')
                return redirect(url_for('auth.register'))
                
        return render_template('register.html', form=form)
        
    except Exception as e:
        current_app.logger.error(f'회원가입 페이지 처리 중 오류 발생: {str(e)}')
        flash('예기치 않은 오류가 발생했습니다. 다시 시도해 주세요.', 'error')
        return redirect(url_for('main.index'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/api/holdings')
@login_required
def get_holdings():
    holdings = StockHolding.query.filter_by(user_id=current_user.id).all()
    return jsonify([holding.to_dict() for holding in holdings])

@main.route('/api/transactions')
@login_required
def get_transactions():
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.timestamp.desc())\
        .limit(20)\
        .all()
    return jsonify([tx.to_dict() for tx in transactions])

@main.route('/leaderboard')
def leaderboard():
    # 모든 사용자의 총 자산을 계산하여 정렬
    users = User.query.all()
    total_users = len(users)  # 전체 사용자 수 계산
    leaderboard_data = []
    
    for user in users:
        try:
            total_assets = user.cash if user.cash is not None else 0
            holdings = StockHolding.query.filter_by(user_id=user.id).all()
            
            for holding in holdings:
                if holding.current_value is not None:
                    total_assets += holding.current_value
            
            # 초기 자본금이 0이면 수익률 산 불가
            if total_assets > 0:
                return_rate = ((total_assets - 10000000) / 10000000) * 100
            else:
                return_rate = 0
            
            leaderboard_data.append({
                'username': user.username or '익명',
                'total_assets': total_assets,
                'return_rate': return_rate
            })
        except Exception as e:
            print(f"Error processing user {user.id}: {str(e)}")
            continue
    
    # 총 자산 기준으로 내림차순 정렬
    leaderboard_data.sort(key=lambda x: x['total_assets'], reverse=True)
    
    # 순위 추가
    for i, data in enumerate(leaderboard_data):
        data['rank'] = i + 1
    
    return render_template('leaderboard.html', 
                         leaderboard=leaderboard_data,
                         total_users=total_users)  # 전체 사용자 수 전달

@main.route('/notifications')
@login_required
def notifications():
    return render_template('notifications.html')

@main.route('/ai-chat')
@login_required
def ai_chat():
    """AI 챗봇 페이지"""
    holdings = StockHolding.query.filter_by(user_id=current_user.id).all()
    
    # 포트폴리오 정보 계산
    total_value = current_user.cash
    invested_amount = 0
    
    holdings_data = []
    for holding in holdings:
        holding_dict = holding.to_dict()
        total_value += holding_dict['total_value']
        invested_amount += holding_dict['avg_price'] * holding_dict['quantity']
        
        holdings_data.append({
            'stock_name': holding_dict['stock_name'],
            'quantity': holding_dict['quantity'],
            'avg_price': holding_dict['avg_price'],
            'current_price': holding_dict['current_price'],
            'total_value': holding_dict['total_value'],
            'return_rate': holding_dict['return_rate'],
            'profit_loss': holding_dict['profit_loss']
        })
    
    # 총 수익률 계산
    total_return_rate = ((total_value - 10000000) / 10000000) * 100
    
    return render_template('ai_chat.html',
        holdings=holdings_data,
        cash=current_user.cash,
        total_assets=total_value,
        invested_amount=invested_amount,
        total_return_rate=total_return_rate
    )

@main.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """AI 챗봇 API 엔드포인트"""
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({
                'success': False,
                'error': '메시지가 비어있습니다.'
            }), 400
            
        # 앱 객체에서 챗봇 인스턴스 가져오기
        chatbot = current_app.chatbot
            
        # 성격 변경 명령 처리
        if message.startswith('성격변경'):
            try:
                _, personality = message.split()
                result = chatbot.set_personality(personality.lower())
                return jsonify({
                    'success': True,
                    'response': result['message'],
                    'type': 'system',
                    'personality': result['personality']
                })
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': "올바른 형식: '성격변경 [positive/negative/neutral]'"
                }), 400
        
        # 일반 메시지 처리
        result = chatbot.chat(message)
        return jsonify({
            'success': True,
            'response': result['message'],
            'type': 'assistant',
            'personality': result['personality']
        })
        
    except Exception as e:
        current_app.logger.error(f"Chat error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500