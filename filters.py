import locale
from datetime import datetime

def init_filters(app):
    """Jinja2 필터 초기화"""
    
    def currency(value):
        """통화 형식으로 변환"""
        try:
            if locale.getlocale()[0] is not None:
                return locale.currency(value, grouping=True)
            else:
                return f"₩{value:,.0f}"
        except:
            return f"₩{value:,.0f}"

    def percentage(value):
        """백분율 형식으로 변환"""
        try:
            return f"{value:+.2f}%"
        except:
            return "0.00%"

    def number_format(value):
        """숫자 형식으로 변환 (천 단위 구분)"""
        try:
            return format(int(value), ',')
        except:
            return '0'

    def format_date(value, format='%Y-%m-%d'):
        """날짜 형식으로 변환"""
        if value is None:
            return ''
        try:
            if isinstance(value, str):
                from datetime import datetime
                value = datetime.strptime(value, '%Y-%m-%d')
            return value.strftime(format)
        except:
            return value

    def format_time(value, format='%H:%M:%S'):
        """시간 형식으로 변환"""
        if value is None:
            return ''
        try:
            if isinstance(value, str):
                from datetime import datetime
                value = datetime.strptime(value, '%H:%M:%S')
            return value.strftime(format)
        except:
            return value

    @app.template_filter('format_number')
    def format_number(value):
        """숫자를 천 단위로 구분하여 포맷팅"""
        try:
            return format(int(value), ',')
        except (ValueError, TypeError):
            return value

    @app.template_filter('format_percentage')
    def format_percentage(value):
        """퍼센트 포맷팅"""
        try:
            return f'{value:,.2f}%'
        except (ValueError, TypeError):
            return value

    @app.template_filter('time_ago')
    def time_ago(value):
        """상대적 시간 표시"""
        if not isinstance(value, datetime):
            return value
            
        now = datetime.utcnow()
        diff = now - value
        
        seconds = diff.total_seconds()
        minutes = int(seconds / 60)
        hours = int(minutes / 60)
        days = int(hours / 24)
        
        if seconds < 60:
            return '방금 전'
        elif minutes < 60:
            return f'{minutes}분 전'
        elif hours < 24:
            return f'{hours}시간 전'
        elif days < 7:
            return f'{days}일 전'
        else:
            return value.strftime('%Y-%m-%d %H:%M')

    @app.template_filter('currency')
    def currency_filter(value):
        """숫자를 통화 형식으로 변환"""
        try:
            return f"{int(value):,}원"
        except (ValueError, TypeError):
            return "0원"
    
    @app.template_filter('number')
    def number_filter(value):
        """숫자를 천단위 구분자가 있는 형식으로 변환"""
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return "0"
    
    @app.template_filter('signed_number')
    def signed_number_filter(value):
        """숫자에 부호를 추가하여 변환"""
        try:
            num = int(value)
            if num > 0:
                return f"+{num:,}"
            return f"{num:,}"
        except (ValueError, TypeError):
            return "0"
    
    @app.template_filter('percentage')
    def percentage_filter(value):
        """숫자를 백분율 형식으로 변환"""
        try:
            return f"{float(value):.2f}%"
        except (ValueError, TypeError):
            return "0.00%"

    # 필터 등록
    app.jinja_env.filters['currency'] = currency
    app.jinja_env.filters['percentage'] = percentage
    app.jinja_env.filters['number_format'] = number_format
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['format_time'] = format_time
    app.jinja_env.filters['format_number'] = format_number
    app.jinja_env.filters['format_percentage'] = format_percentage
    app.jinja_env.filters['time_ago'] = time_ago
    app.jinja_env.filters['currency'] = currency_filter
    app.jinja_env.filters['number'] = number_filter
    app.jinja_env.filters['signed_number'] = signed_number_filter
    app.jinja_env.filters['percentage'] = percentage_filter