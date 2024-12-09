import { socket, initializeSocket } from './common/socket.js';
import { stocks, portfolio } from './common/socket.js';

const app = {
    selectedStock: null,
    priceChart: null,
    currentPrice: 0,
    orderType: 'buy',
    isInitialized: false,
    historyCache: {},

    init: async function() {
        if (this.isInitialized) {
            console.log('App already initialized');
            return;
        }

        const priceChartElement = document.getElementById('priceChart');
        if (!priceChartElement) {
            console.log('Not on market page, skipping initialization');
            return;
        }

        try {
            await this.waitForToast();
            console.log('Toast is loaded successfully');
            
            this.initStyles();
            await this.initChart();
            this.setupEventListeners();
            this.setupSearchFunction();
            
            await initializeSocket(this);
            
            this.isInitialized = true;
            console.log('Market app initialized successfully');
        } catch (error) {
            console.error('Failed to initialize market app:', error);
        }
    },

    initChart: async function() {
        const canvas = document.getElementById('priceChart');
        if (!canvas) {
            console.warn('Price chart canvas not found');
            return;
        }

        try {
            const ctx = canvas.getContext('2d');
            this.priceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: '주가',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1,
                        borderWidth: 2,
                        pointRadius: 1,
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                label: function(context) {
                                    return `${context.parsed.y.toLocaleString()}원`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: false,
                            ticks: {
                                callback: function(value) {
                                    return value.toLocaleString() + '원';
                                }
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
            console.log('Chart initialized successfully');
        } catch (error) {
            console.error('Error initializing chart:', error);
            throw error;
        }
    },

    formatChartTime: function(timestamp) {
        const date = new Date(timestamp);
        if (isNaN(date.getTime())) {
            return timestamp;
        }
        return date.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    },

    initializeChartWithHistory: function(history) {
        if (!this.priceChart || !history || !Array.isArray(history)) {
            console.warn('Invalid chart data:', { chart: !!this.priceChart, history });
            return;
        }

        try {
            console.log('Initializing chart with history:', history);
            
            const sortedHistory = [...history].sort((a, b) => {
                const timeA = new Date(a.timestamp).getTime();
                const timeB = new Date(b.timestamp).getTime();
                return timeA - timeB;
            });

            this.priceChart.data.labels = sortedHistory.map(item => 
                this.formatChartTime(item.timestamp)
            );
            
            this.priceChart.data.datasets[0].data = sortedHistory.map(item => parseFloat(item.price));

            const prices = this.priceChart.data.datasets[0].data;
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            const padding = (maxPrice - minPrice) * 0.1;

            this.priceChart.options.scales.y.min = Math.floor(minPrice - padding);
            this.priceChart.options.scales.y.max = Math.ceil(maxPrice + padding);

            this.priceChart.update();
            console.log('Chart updated with history data:', {
                labels: this.priceChart.data.labels,
                data: this.priceChart.data.datasets[0].data
            });
        } catch (error) {
            console.error('Error updating chart with history:', error);
            console.error('History data:', history);
        }
    },

    appendPriceToChart: function(priceData) {
        if (!this.priceChart) return;

        try {
            const timeString = this.formatChartTime(priceData.timestamp);

            if (this.priceChart.data.labels.length > 100) {
                this.priceChart.data.labels.shift();
                this.priceChart.data.datasets[0].data.shift();
            }

            this.priceChart.data.labels.push(timeString);
            this.priceChart.data.datasets[0].data.push(parseFloat(priceData.price));

            const prices = this.priceChart.data.datasets[0].data;
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            const padding = (maxPrice - minPrice) * 0.1;

            this.priceChart.options.scales.y.min = Math.floor(minPrice - padding);
            this.priceChart.options.scales.y.max = Math.ceil(maxPrice + padding);

            this.priceChart.update('none');
        } catch (error) {
            console.error('Error appending price to chart:', error);
        }
    },

    setupSearchFunction: function() {
        const searchInput = document.getElementById('stockSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const searchTerm = e.target.value.toLowerCase();
                document.querySelectorAll('.stock-item').forEach(item => {
                    const name = item.querySelector('.stock-name').textContent.toLowerCase();
                    const code = item.querySelector('.stock-code').textContent.toLowerCase();
                    const shouldShow = name.includes(searchTerm) || code.includes(searchTerm);
                    item.style.display = shouldShow ? 'block' : 'none';
                });
            });
        }
    },

    updateStockList: function(stocks) {
        console.log('Updating stock list:', stocks);
        stocks.forEach(stock => {
            const stockItem = document.querySelector(`[data-code="${stock.code}"]`);
            if (stockItem) {
                stockItem.dataset.price = stock.price;
                stockItem.dataset.priceDiff = stock.price_diff;
                stockItem.dataset.changeRate = stock.change_rate;

                const priceElement = stockItem.querySelector('.stock-price');
                const changeElement = stockItem.querySelector('.stock-change');

                if (priceElement) {
                    priceElement.textContent = `${this.numberWithCommas(stock.price)}원`;
                }
                if (changeElement) {
                    const changeHTML = stock.price_diff > 0 
                        ? `<span class="positive">+${this.numberWithCommas(stock.price_diff)}원 (+${stock.change_rate.toFixed(2)}%)</span>`
                        : stock.price_diff < 0
                        ? `<span class="negative">${this.numberWithCommas(stock.price_diff)}원 (${stock.change_rate.toFixed(2)}%)</span>`
                        : `<span>0원 (0.00%)</span>`;
                    changeElement.innerHTML = changeHTML;
                }

                if (this.selectedStock && this.selectedStock.code === stock.code) {
                    this.updateSelectedStockInfo(stock);
                }
            }
        });
    },

    updateSelectedStockInfo: function(stock, isInitial = false) {
        console.log('Updating selected stock info:', stock);
        this.selectedStock = stock;
        this.currentPrice = stock.price;

        document.querySelectorAll('.stock-item').forEach(item => {
            item.classList.toggle('selected', item.dataset.code === stock.code);
        });

        const nameElement = document.getElementById('selectedStockName');
        const codeElement = document.getElementById('selectedStockCode');
        const priceElement = document.getElementById('selectedStockPrice');
        const changeElement = document.getElementById('selectedStockChange');

        if (nameElement) nameElement.textContent = stock.name;
        if (codeElement) codeElement.textContent = stock.code;
        if (priceElement) priceElement.textContent = `${this.numberWithCommas(stock.price)}원`;
        if (changeElement) {
            const changeHTML = stock.price_diff > 0 
                ? `<span class="positive">+${this.numberWithCommas(stock.price_diff)}원 (+${stock.change_rate.toFixed(2)}%)</span>`
                : stock.price_diff < 0
                ? `<span class="negative">${this.numberWithCommas(stock.price_diff)}원 (${stock.change_rate.toFixed(2)}%)</span>`
                : `<span>0원 (0.00%)</span>`;
            changeElement.innerHTML = changeHTML;
        }

        const tradeButton = document.getElementById('tradeButton');
        if (tradeButton) {
            tradeButton.disabled = false;
            this.updateOrderSummary();
        }

        if (isInitial) {
            socket.emit('select_stock', { 
                code: stock.code,
                initial: true
            });
        }
    },

    setupEventListeners: function() {
        document.querySelectorAll('.stock-item').forEach(item => {
            item.addEventListener('click', () => {
                const stockData = {
                    code: item.dataset.code,
                    name: item.dataset.name,
                    price: parseInt(item.dataset.price),
                    price_diff: parseInt(item.dataset.priceDiff),
                    change_rate: parseFloat(item.dataset.changeRate)
                };
                this.updateSelectedStockInfo(stockData, true);
            });
        });

        socket.on('stock_selected', (data) => {
            console.log('Received stock data:', data);
            if (data.history) {
                this.initializeChartWithHistory(data.history);
            }
            if (data.latest_price) {
                this.appendPriceToChart({
                    timestamp: new Date(),
                    price: data.latest_price.price
                });
            }
        });

        socket.on('market_data', (data) => {
            console.log('Received market data:', data);
            if (data.stocks) {
                this.updateStockList(data.stocks);
                if (this.selectedStock) {
                    const updatedStock = data.stocks.find(s => s.code === this.selectedStock.code);
                    if (updatedStock) {
                        this.appendPriceToChart({
                            timestamp: new Date(),
                            price: updatedStock.price
                        });
                    }
                }
            }
            if (data.holdings) {
                this.updatePortfolioUI();
            }
        });

        const tradeForm = document.getElementById('tradeForm');
        if (tradeForm) {
            tradeForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleTradeSubmit();
            });
        }

        document.querySelectorAll('.trade-type-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.trade-type-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                this.orderType = tab.dataset.type;
                
                const tradeButton = document.getElementById('tradeButton');
                if (tradeButton) {
                    tradeButton.textContent = this.orderType === 'buy' ? '매수하기' : '매도하기';
                    tradeButton.className = `trade-button ${this.orderType}`;
                }
                
                this.updateOrderSummary();
            });
        });

        const quantityInput = document.getElementById('quantity');
        if (quantityInput) {
            quantityInput.addEventListener('input', () => this.updateOrderSummary());
        }
    },

    handleTradeSubmit: function() {
        if (!this.selectedStock) {
            this.showNotification('주식을 선택해주세요.', 'error');
            return;
        }

        const quantity = parseInt(document.getElementById('quantity').value);
        if (!quantity || quantity <= 0) {
            this.showNotification('올바른 수량을 입력해주세요.', 'error');
            return;
        }

        const tradeData = {
            stock_code: this.selectedStock.code,
            quantity: quantity,
            type: this.orderType.toUpperCase()
        };

        console.log('Sending trade request:', tradeData);
        socket.emit('trade', tradeData);
    },

    updateOrderSummary: function() {
        if (!this.selectedStock) return;

        const quantity = parseInt(document.getElementById('quantity').value) || 0;
        const total = quantity * this.currentPrice;

        document.getElementById('summaryQuantity').textContent = `${this.numberWithCommas(quantity)}주`;
        document.getElementById('summaryPrice').textContent = `${this.numberWithCommas(this.currentPrice)}원`;
        document.getElementById('summaryTotal').textContent = `${this.numberWithCommas(total)}원`;

        if (this.orderType === 'sell') {
            const holding = portfolio.holdings?.find(h => h.stock_code === this.selectedStock.code);
            const tradeButton = document.getElementById('tradeButton');
            if (tradeButton) {
                tradeButton.disabled = !holding || quantity > holding.quantity;
            }
        }
    },

    updatePortfolioUI: function() {
        const holdingsTableBody = document.getElementById('holdingsTableBody');
        if (!holdingsTableBody) return;

        if (!portfolio.holdings || portfolio.holdings.length === 0) {
            holdingsTableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-holdings">
                        <p>보유중인 주식이 없습니다.</p>
                    </td>
                </tr>
            `;
            return;
        }

        const holdingsHTML = portfolio.holdings.map(holding => `
            <tr>
                <td>${holding.stock_name}</td>
                <td>${this.numberWithCommas(holding.quantity)}주</td>
                <td>${this.numberWithCommas(holding.avg_price)}원</td>
                <td>${this.numberWithCommas(holding.current_price)}원</td>
                <td>${this.numberWithCommas(holding.total_value)}원</td>
                <td class="${holding.return_rate >= 0 ? 'positive' : 'negative'}">
                    ${holding.return_rate >= 0 ? '+' : ''}${holding.return_rate.toFixed(2)}%
                </td>
                <td class="${holding.profit_loss >= 0 ? 'positive' : 'negative'}">
                    ${holding.profit_loss >= 0 ? '+' : ''}${this.numberWithCommas(holding.profit_loss)}원
                </td>
            </tr>
        `).join('');

        holdingsTableBody.innerHTML = holdingsHTML;

        const navCashAmount = document.getElementById('navCashAmount');
        if (navCashAmount && portfolio.cash !== undefined) {
            navCashAmount.textContent = this.numberWithCommas(portfolio.cash);
        }
    },

    handleTradeSuccess: function(response) {
        console.log('Trade success:', response);
        if (response.status === 'success') {
            this.showNotification(response.message, 'success');
            
            if (response.portfolio) {
                this.updatePortfolioUI();
                
                const quantityInput = document.getElementById('quantity');
                if (quantityInput) {
                    quantityInput.value = '';
                    this.updateOrderSummary();
                }
            }
        } else {
            this.showNotification(response.message || '거래 처리 중 오류가 발생했습니다.', 'error');
        }
    },

    numberWithCommas: function(x) {
        return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },

    waitForToast: function() {
        return new Promise((resolve, reject) => {
            if (window.Toast) {
                resolve(window.Toast);
                return;
            }
            
            const checkToast = setInterval(() => {
                if (window.Toast) {
                    clearInterval(checkToast);
                    resolve(window.Toast);
                }
            }, 100);
            
            setTimeout(() => {
                clearInterval(checkToast);
                reject(new Error('Toast initialization timeout'));
            }, 10000);
        });
    },

    showNotification: async function(message, type) {
        try {
            const toast = await this.waitForToast();
            if (toast) {
                toast.show(message, type);
            }
        } catch (error) {
            console.error('Error showing notification:', error);
        }
    },

    initStyles: function() {
        if (!document.getElementById('market-styles')) {
            const style = document.createElement('style');
            style.id = 'market-styles';
            style.textContent = `
                .toast-notification {
                    position: fixed;
                    bottom: 20px !important;
                    right: 20px;
                    z-index: 9999;
                    background: white;
                    padding: 15px 25px;
                    border-radius: 4px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    font-size: 14px;
                    max-width: 350px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    opacity: 0;
                    transform: translateY(100%);
                    transition: all 0.3s ease;
                }

                .toast-notification.show {
                    opacity: 1;
                    transform: translateY(0);
                }

                .toast-notification.success {
                    background-color: #4CAF50;
                    color: white;
                }

                .toast-notification.error {
                    background-color: #F44336;
                    color: white;
                }
            `;
            document.head.appendChild(style);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => app.init());

export { app };

