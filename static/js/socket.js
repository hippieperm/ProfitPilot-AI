// socket.io는 base.html에서 전역으로 로드됨
const socket = io({
    transports: ['websocket', 'polling'],
    path: '/socket.io/',
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
});

// 소켓 이벤트 리스너 설정
function setupSocketListeners() {
    console.log('Setting up socket listeners');
    
    socket.on('connect', () => {
        console.log('Socket connected');
        joinUserRoom();
    });

    socket.on('connect_error', (error) => {
        console.error('Socket connection error:', error);
    });

    socket.on('disconnect', (reason) => {
        console.log('Socket disconnected:', reason);
    });

    socket.on('market_data', (data) => {
        console.log('Market data received:', data);
        if (data.stocks) {
            console.log('Updating stocks:', data.stocks);
            window.dispatchEvent(new CustomEvent('stocksUpdated', { detail: data.stocks }));
        }
        if (data.holdings) {
            console.log('Updating portfolio:', data.holdings);
            window.dispatchEvent(new CustomEvent('portfolioUpdated', { detail: data.holdings }));
        }
        if (data.leaderboard) {
            console.log('Updating leaderboard:', data.leaderboard);
            window.dispatchEvent(new CustomEvent('leaderboardUpdated', { detail: data.leaderboard }));
        }
    });

    socket.on('trade_success', (data) => {
        console.log('Trade success:', data);
        window.dispatchEvent(new CustomEvent('tradeSuccess', { detail: data }));
    });

    socket.on('trade_error', (error) => {
        console.log('Trade error:', error);
        window.dispatchEvent(new CustomEvent('tradeError', { detail: error }));
    });
}

// 사용자 룸 참가
function joinUserRoom() {
    const userIdMeta = document.querySelector('meta[name="user-id"]');
    if (userIdMeta) {
        const userId = userIdMeta.getAttribute('content');
        socket.emit('join', { room: `user_${userId}` });
    }
}

// 초기화
setupSocketListeners();

export { socket }; 