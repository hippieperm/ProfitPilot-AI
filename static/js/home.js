import { socket, initializeSocket } from './common/socket.js';

document.addEventListener('DOMContentLoaded', async function() {
    try {
        await initializeSocket();
        setupSocketListeners();
        initializeUI();
        updateCurrentTime();
        setInterval(updateCurrentTime, 1000);
        console.log('Home page initialized successfully');
    } catch (error) {
        console.error('Failed to initialize home page:', error);
    }
});

// 소켓 이벤트 리스너 설정
function setupSocketListeners() {
    socket.on('market_data', (data) => {
        if (data.stocks) {
            updateMarketOverview(data.stocks);
            updateStockHighlights(data.stocks);
        }
        if (data.total_users) {
            updateUserStats(data.total_users);
        }
    });

    console.log('Socket listeners initialized');
}

// UI 초기화
function initializeUI() {
    // 초기값 설정
    document.getElementById('total-users').textContent = '0';
    document.getElementById('up-stocks').textContent = '0';
    document.getElementById('down-stocks').textContent = '0';
}

// 현재 시간 업데이트
function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('current-time').textContent = timeString;
}

// 시장 개요 업데이트
function updateMarketOverview(stocks) {
    if (!Array.isArray(stocks)) {
        console.error('Invalid stocks data:', stocks);
        return;
    }

    // 시장 규모 계산
    const totalMarketCap = stocks.reduce((sum, stock) => {
        const price = parseFloat(stock.price) || 0;
        return sum + (price * 100000);
    }, 0);
    document.getElementById('total-market-cap').textContent = formatCurrency(totalMarketCap);

    // 상승/하락 종목 수 계산
    const trends = stocks.reduce((acc, stock) => {
        const priceDiff = parseFloat(stock.price_diff) || 0;
        if (priceDiff > 0) acc.up++;
        else if (priceDiff < 0) acc.down++;
        return acc;
    }, { up: 0, down: 0 });

    document.getElementById('up-stocks').textContent = trends.up.toString();
    document.getElementById('down-stocks').textContent = trends.down.toString();
}

// 사용자 통계 업데이트
function updateUserStats(totalUsers) {
    const total = parseInt(totalUsers) || 0;
    document.getElementById('total-users').textContent = formatNumber(total);
}

// 주요 종목 현황 업데이트
function updateStockHighlights(stocks) {
    if (!Array.isArray(stocks)) return;
    
    // 급등 종목
    const topGainers = [...stocks]
        .sort((a, b) => (parseFloat(b.change_rate) || 0) - (parseFloat(a.change_rate) || 0))
        .slice(0, 5);
    
    // 급락 종목
    const topLosers = [...stocks]
        .sort((a, b) => (parseFloat(a.change_rate) || 0) - (parseFloat(b.change_rate) || 0))
        .slice(0, 5);

    // 급등 종목 업데이트
    document.getElementById('top-gainers').innerHTML = topGainers.map(stock => `
        <div class="highlight-item">
            <div class="stock-info">
                <span class="stock-name">${stock.name}</span>
                <span class="stock-code">${stock.code}</span>
            </div>
            <div class="stock-change positive">+${(parseFloat(stock.change_rate) || 0).toFixed(2)}%</div>
        </div>
    `).join('');

    // 급락 종목 업데이트
    document.getElementById('top-losers').innerHTML = topLosers.map(stock => `
        <div class="highlight-item">
            <div class="stock-info">
                <span class="stock-name">${stock.name}</span>
                <span class="stock-code">${stock.code}</span>
            </div>
            <div class="stock-change negative">${(parseFloat(stock.change_rate) || 0).toFixed(2)}%</div>
        </div>
    `).join('');
}

// 포맷팅 함수들
function formatCurrency(value) {
    return new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: 'KRW',
        maximumFractionDigits: 0
    }).format(value);
}

function formatNumber(value) {
    return new Intl.NumberFormat('ko-KR').format(value);
}