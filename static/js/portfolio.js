import { socket, initializeSocket } from './common/socket.js';
import { formatNumber } from './common/formatters.js';

const app = {
    isInitialized: false,

    init: async function() {
        if (this.isInitialized) return;

        try {
            await initializeSocket(this);
            this.setupEventListeners();
            this.isInitialized = true;
            console.log('Portfolio initialized successfully');
        } catch (error) {
            console.error('Failed to initialize portfolio:', error);
        }
    },

    setupEventListeners: function() {
        // 초기 연결 시 포트폴리오 데이터 요청
        socket.on('connect', () => {
            console.log('Requesting portfolio data...');
            socket.emit('request_market_data');
        });

        // 마켓 데이터 수신 시 포트폴리오 업데이트
        socket.on('market_data', (data) => {
            console.log('Received market data for portfolio:', data);
            if (data.holdings) {
                this.updatePortfolio(data);
            }
        });

        // 거래 성공 시 포트폴리오 업데이트
        socket.on('trade_success', (data) => {
            console.log('Trade success, updating portfolio:', data);
            if (data.portfolio) {
                this.updatePortfolio(data.portfolio);
            }
        });
    },

    updatePortfolio: function(data) {
        // 계좌 요약 업데이트
        this.updateSummary(data);
        
        // 보유 주식 업데이트
        this.updateHoldings(data.holdings);
    },

    updateSummary: function(data) {
        // 총 자산 업데이트
        const totalAssetsElement = document.querySelector('.summary-card:nth-child(1) .value');
        if (totalAssetsElement && data.total_assets !== undefined) {
            totalAssetsElement.textContent = `${formatNumber(data.total_assets)}원`;
        }

        // 보유 현금 업데이트
        const cashElement = document.querySelector('.summary-card:nth-child(2) .value');
        if (cashElement && data.cash !== undefined) {
            cashElement.textContent = `${formatNumber(data.cash)}원`;
        }

        // 투자 자산 업데이트
        const investedElement = document.querySelector('.summary-card:nth-child(3) .value');
        if (investedElement && data.invested_amount !== undefined) {
            investedElement.textContent = `${formatNumber(data.invested_amount)}원`;
        }

        // 총 수익률 업데이트
        const returnRateElement = document.querySelector('.summary-card:nth-child(4) .value');
        if (returnRateElement && data.total_return_rate !== undefined) {
            const returnRate = data.total_return_rate;
            returnRateElement.textContent = `${returnRate >= 0 ? '+' : ''}${returnRate.toFixed(2)}%`;
            returnRateElement.className = `value ${returnRate >= 0 ? 'positive' : 'negative'}`;
        }
    },

    updateHoldings: function(holdings) {
        const tbody = document.querySelector('.table-responsive table tbody');
        if (!tbody) return;

        if (!holdings || holdings.length === 0) {
            // 보유 주식이 없는 경우
            const tableContainer = document.querySelector('.table-responsive');
            if (tableContainer) {
                tableContainer.innerHTML = `
                    <div class="empty-state">
                        <p>보유중인 주식이 없습니다.</p>
                        <a href="/market" class="btn btn-primary">거래하러 가기</a>
                    </div>
                `;
            }
            return;
        }

        // 보유 주식 목록 업데이트
        tbody.innerHTML = holdings.map(holding => `
            <tr>
                <td>${holding.stock_name}</td>
                <td>${holding.quantity}주</td>
                <td>${formatNumber(holding.avg_price)}원</td>
                <td>${formatNumber(holding.current_price)}원</td>
                <td>${formatNumber(holding.total_value)}원</td>
                <td class="${holding.return_rate >= 0 ? 'positive' : 'negative'}">
                    ${holding.return_rate >= 0 ? '+' : ''}${holding.return_rate.toFixed(2)}%
                </td>
                <td class="${holding.profit_loss >= 0 ? 'positive' : 'negative'}">
                    ${holding.profit_loss >= 0 ? '+' : ''}${formatNumber(holding.profit_loss)}원
                </td>
            </tr>
        `).join('');

        console.log('Holdings updated successfully');
    }
};

// DOM이 로드되면 앱 초기화
document.addEventListener('DOMContentLoaded', () => app.init());

export { app }; 