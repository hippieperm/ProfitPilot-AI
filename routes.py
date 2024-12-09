from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import StockHolding, Transaction, User

main = Blueprint('main', __name__)

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

        total_return_rate = ((total_assets - 10000000) / 10000000) * 100 if total_assets > 0 else 0

        return {
            'holdings': holdings_data,
            'total_assets': total_assets,
            'invested_amount': invested_amount,
            'total_return_rate': total_return_rate,
            'cash': user.cash
        }
    except Exception as e:
        current_app.logger.error(f"포트폴리오 데이터 계산 중 오류 발생 (User ID: {user.id}): {str(e)}")
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
        context = {'stocks': [], 'portfolio': None}
        if current_user.is_authenticated:
            context['portfolio'] = calculate_portfolio_data(current_user)
        return render_template('home.html', **context)
    except Exception as e:
        print(f"Critical error in index route: {str(e)}")
        return render_template('home.html', stocks=[], portfolio=None)

@main.route('/market')
@login_required
def market():
    try:
        stocks = stock_data.get_all_stocks()
        portfolio_data = calculate_portfolio_data(current_user)
        return render_template('market.html', stocks=stocks, holdings=portfolio_data.get('holdings', []))
    except Exception as e:
        current_app.logger.error(f"Error in market route: {str(e)}")
        flash('거래소 정보를 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('main.index'))

@main.route('/portfolio')
@login_required
def portfolio():
    try:
        portfolio_data = calculate_portfolio_data(current_user)
        transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(10).all()
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
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).all()
    total_amount = sum(tx.total_amount for tx in transactions)
    return render_template('transactions.html', transactions=transactions, total_amount=total_amount)

@main.route('/leaderboard')
def leaderboard():
    users = User.query.all()
    total_users = len(users)
    leaderboard_data = []

    for user in users:
        try:
            total_assets = user.cash if user.cash is not None else 0
            holdings = StockHolding.query.filter_by(user_id=user.id).all()
            for holding in holdings:
                if holding.current_value is not None:
                    total_assets += holding.current_value
            return_rate = ((total_assets - 10000000) / 10000000) * 100 if total_assets > 0 else 0
            leaderboard_data.append({
                'username': user.username or '익명',
                'total_assets': total_assets,
                'return_rate': return_rate
            })
        except Exception as e:
            print(f"Error processing user {user.id}: {str(e)}")
            continue

    leaderboard_data.sort(key=lambda x: x['total_assets'], reverse=True)
    for i, data in enumerate(leaderboard_data):
        data['rank'] = i + 1

    return render_template('leaderboard.html', leaderboard=leaderboard_data, total_users=total_users)

@main.route('/notifications')
@login_required
def notifications():
    return render_template('notifications.html')
