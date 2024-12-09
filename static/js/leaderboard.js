import { socket, initializeSocket } from './common/socket.js';
import { formatNumber } from './common/formatters.js';

const app = {
    isInitialized: false,
    currentUsername: document.querySelector('.leaderboard-container').dataset.username,

    init: async function() {
        if (this.isInitialized) return;

        try {
            await initializeSocket(this);
            this.setupEventListeners();
            this.isInitialized = true;
            console.log('Leaderboard initialized successfully');
        } catch (error) {
            console.error('Failed to initialize leaderboard:', error);
        }
    },

    setupEventListeners: function() {
        // 초기 연결 시 리더보드 데이터 요청
        socket.on('connect', () => {
            console.log('Requesting leaderboard data...');
            socket.emit('request_leaderboard');
        });

        // 마켓 데이터 수신 시 리더보드 업데이트
        socket.on('market_data', (data) => {
            console.log('Received market data for leaderboard:', data);
            if (data.leaderboard) {
                this.updateLeaderboardTable(data.leaderboard, data.total_users);
            }
        });
    },

    updateLeaderboardTable: function(leaderboard, totalUsers) {
        const tbody = document.getElementById('leaderboardTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = leaderboard.map(entry => `
            <tr class="leaderboard-row ${this.currentUsername === entry.username ? 'highlight' : ''}">
                <td class="rank">
                    ${entry.rank <= 3 
                        ? `<span class="rank-badge rank-${entry.rank}">${entry.rank}</span>`
                        : `<span class="rank-number">#${entry.rank}</span>`
                    }
                </td>
                <td class="username">
                    ${entry.username}
                    ${this.currentUsername === entry.username ? '<span class="user-badge">(나)</span>' : ''}
                </td>
                <td class="total-assets">${formatNumber(entry.total_assets)}원</td>
                <td class="return-rate ${entry.return_rate >= 0 ? 'positive' : 'negative'}">
                    ${entry.return_rate >= 0 ? '+' : ''}${entry.return_rate.toFixed(2)}%
                </td>
            </tr>
        `).join('');

        // 전체 사용자 수 업데이트
        const description = document.querySelector('.section-description');
        if (description && totalUsers) {
            description.textContent = `현재 ${formatNumber(totalUsers)}명의 투자자들과 경쟁 중입니다`;
        }

        console.log('Leaderboard updated successfully');
    }
};

// DOM이 로드되면 앱 초기화
document.addEventListener('DOMContentLoaded', () => app.init());

export { app }; 