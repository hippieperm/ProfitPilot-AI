// 전역 상태 관리
let stocks = {};
let portfolio = {};

// 소켓 상태 관리
const socketState = {
    isConnected: false,
    currentRoom: null,
    reconnectAttempts: 0,
    isInitialized: false,
    app: null
};

// 소켓 초기화
export const socket = io({
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000,
    autoConnect: false,
    transports: ['websocket']
});

export { stocks, portfolio };

export function resetSocketState() {
    socketState.isConnected = false;
    socketState.currentRoom = null;
    socketState.reconnectAttempts = 0;
}

export function initializeSocket(appInstance = null) {
    if (socketState.isInitialized && socketState.app === appInstance) {
        console.log('Socket already initialized with this app instance');
        return;
    }

    console.log('Initializing socket...');
    socketState.app = appInstance;
    
    if (!socket.connected) {
        socket.connect();
    }
    
    if (!socketState.isInitialized) {
        setupSocketListeners();
    }
}

function setupSocketListeners() {
    if (socketState.isInitialized) {
        console.log('Socket listeners already initialized');
        return;
    }
    
    socketState.isInitialized = true;
    console.log('Setting up socket listeners');

    // 연결 이벤트
    socket.on('connect', () => {
        console.log('Socket connected');
        socketState.isConnected = true;
        socketState.reconnectAttempts = 0;
        
        // 사용자 ID 가져오기
        const userId = document.querySelector('meta[name="user-id"]')?.content;
        if (userId && socketState.currentRoom !== `user_${userId}`) {
            // room에 join
            socket.emit('join', { room: `user_${userId}` });
            socketState.currentRoom = `user_${userId}`;
            console.log(`Joined room: ${socketState.currentRoom}`);
        }
        
        // 초기 데이터 요청
        socket.emit('request_market_data');
        socket.emit('request_portfolio_data');
    });

    // 시장 데이터 업데이트
    socket.on('market_data', (data) => {
        console.log('Market data received:', data);

        // 주식 데이터 업데이트
        if (data.stocks) {
            console.log('Updating stocks:', data.stocks);
            stocks = data.stocks;
            if (socketState.app?.updateStockPrices) {
                socketState.app.updateStockPrices(data.stocks);
            }
        }

        // 포트폴리오 데이터 업데이트
        if (data.holdings) {
            console.log('Updating portfolio:', data.holdings);
            portfolio.holdings = data.holdings;
            portfolio.cash = data.cash;
            portfolio.total_assets = data.total_assets;
            portfolio.invested_amount = data.invested_amount;

            if (socketState.app?.updatePortfolioUI) {
                socketState.app.updatePortfolioUI();
            }
        }

        // 리더보드 데이터 업데이트 추가
        if (data.leaderboard) {
            console.log('Updating leaderboard:', data.leaderboard);
            if (socketState.app?.updateLeaderboardTable) {
                socketState.app.updateLeaderboardTable(data.leaderboard, data.total_users);
            }
        }
    });

    // 거래 성공 이벤트
    socket.on('trade_success', (response) => {
        console.log('Trade success:', response);
        if (socketState.app?.handleTradeSuccess) {
            socketState.app.handleTradeSuccess(response);
        }
    });

    // 거래 실패 이벤트
    socket.on('trade_error', (response) => {
        console.log('Trade error:', response);
        if (socketState.app?.showNotification) {
            socketState.app.showNotification(response.message || '거래 처리 중 오류가 발생했습니다.', 'error');
        }
    });

    // 연결 오류 처리
    socket.on('connect_error', (error) => {
        console.error('Socket connection error:', error);
        socketState.reconnectAttempts++;
        if (socketState.app?.showNotification) {
            socketState.app.showNotification('서버 연결에 실패했습니다. 재연결을 시도합니다.', 'error');
        }
    });

    // 연결 끊김 처리
    socket.on('disconnect', (reason) => {
        console.log('Socket disconnected:', reason);
        resetSocketState();
        if (socketState.app?.showNotification) {
            socketState.app.showNotification('서버와의 연결이 끊어졌습니다. 재연결을 시도합니다.', 'error');
        }
    });
} 