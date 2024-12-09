import { socket, initializeSocket } from './common/socket.js';
import { showNotification } from './common/notification.js';
import { formatCurrency, formatNumber } from './common/formatters.js';

// UI 업데이트 함수
function updateUI() {
    const currentPage = window.location.pathname;
    
    if (currentPage === '/' || currentPage === '/home') {
        if (typeof updateHomeUI === 'function') {
            updateHomeUI(stocks);
        }
    } else if (currentPage === '/market') {
        if (typeof updateMarketUI === 'function') {
            updateMarketUI(stocks);
        }
    }
}

// 포트폴리오 UI 업데이트
function updatePortfolioUI() {
    // 포트폴리오 정보 업데이트
    if (typeof updatePortfolio === 'function') {
        updatePortfolio(portfolio);
    }
    
    // 플레이어 스탯 업데이트
    if (typeof updatePlayerStats === 'function') {
        updatePlayerStats(portfolio);
    }
    
    // 보유 주식 목록 업데이트
    if (typeof updateHoldings === 'function') {
        updateHoldings(portfolio.stocks);
    }
}

// 시장 통계 업데이트
function updateMarketStats(stats) {
    const elements = {
        marketValue: document.getElementById('market-value'),
        totalVolume: document.getElementById('total-volume'),
        tradeCount: document.getElementById('trade-count'),
        userCount: document.getElementById('user-count')
    };

    if (elements.marketValue) {
        elements.marketValue.textContent = formatCurrency(stats.market_value);
    }
    if (elements.totalVolume) {
        elements.totalVolume.textContent = formatNumber(stats.total_volume);
    }
    if (elements.tradeCount) {
        elements.tradeCount.textContent = formatNumber(stats.trade_count);
    }
    if (elements.userCount) {
        elements.userCount.textContent = formatNumber(stats.user_count);
    }
}

function cleanup() {
    if (socket) {
        socket.off('market_data');
        socket.off('portfolio_update');
        socket.off('chart_update');
        socket.off('news_update');
        socket.off('user_update');
        socket.off('trade_success');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    cleanup();  // 이전 리스너 정리
    
    // 저장된 테마 설정 불러오기
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
});

// 주식 가격 업데이트 함수
function updateStockPrice(data) {
    const priceElement = document.getElementById(`price-${data.stock_code}`);
    const changeElement = document.getElementById(`change-${data.stock_code}`);
    
    if (priceElement && changeElement) {
        const oldPrice = parseFloat(priceElement.textContent.replace(/[^0-9.-]+/g, ''));
        const newPrice = parseFloat(data.price);
        
        // 가격 업데이트
        priceElement.textContent = `${numberWithCommas(newPrice)}원`;
        
        // 변동률 계산 및 업데이트
        const diff = newPrice - data.prev_price;
        const changeRate = (diff / data.prev_price) * 100;
        
        let changeHTML = '';
        if (diff > 0) {
            changeHTML = `<span class="positive">+${numberWithCommas(diff)}원 (+${changeRate.toFixed(2)}%)</span>`;
        } else if (diff < 0) {
            changeHTML = `<span class="negative">${numberWithCommas(diff)}원 (${changeRate.toFixed(2)}%)</span>`;
        } else {
            changeHTML = `<span>0원 (0.00%)</span>`;
        }
        changeElement.innerHTML = changeHTML;
        
        // 가격 변동 효과
        priceElement.classList.add('value-update');
        setTimeout(() => priceElement.classList.remove('value-update'), 1000);
    }
}

// 숫자 포맷팅
function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
