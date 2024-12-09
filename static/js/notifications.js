document.addEventListener('DOMContentLoaded', function() {
    // 소켓 연결
    const socket = io();
    
    // 알림 카운터 업데이트
    function updateNotificationCount() {
        const unreadCount = document.querySelectorAll('.notification-card.unread').length;
        const counter = document.getElementById('notification-counter');
        if (counter) {
            counter.textContent = unreadCount;
            counter.style.display = unreadCount > 0 ? 'block' : 'none';
        }
    }
    
    // 알림 목록 업데이트
    function updateNotificationsList(notifications) {
        const container = document.querySelector('.notifications-list');
        if (!container) return;
        
        if (notifications.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>새로운 알림이 없습니다.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = notifications.map(notification => `
            <div class="notification-card ${notification.is_read ? '' : 'unread'}" data-id="${notification.id}">
                <div class="notification-icon">
                    <i class="fas fa-${getNotificationIcon(notification.type)}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-header">
                        <h4 class="notification-title">${notification.title}</h4>
                        <span class="notification-time">${timeAgo(notification.created_at)}</span>
                    </div>
                    <p class="notification-message">${notification.message}</p>
                </div>
                ${!notification.is_read ? `
                    <button class="mark-read" title="읽음 표시">
                        <i class="fas fa-check"></i>
                    </button>
                ` : ''}
            </div>
        `).join('');
        
        // 이벤트 리스너 다시 설정
        attachNotificationEventListeners();
        updateNotificationCount();
    }
    
    // 활성화된 알림 목록 업데이트
    function updateActiveAlerts(alerts) {
        const container = document.querySelector('.alerts-grid');
        if (!container) return;
        
        if (!alerts.length) {
            container.innerHTML = '<p class="empty-state">설정된 가격 알림이 없습니다.</p>';
            return;
        }
        
        container.innerHTML = alerts.map(alert => `
            <div class="alert-card">
                <div class="alert-header">
                    <span class="stock-code">${alert.stock_code}</span>
                    <button class="delete-alert" data-alert-id="${alert.id}">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="alert-body">
                    <p class="condition">${alert.condition === 'above' ? '이상' : '이하'}</p>
                    <p class="target-price">${formatNumber(alert.target_price)}원</p>
                </div>
                <div class="alert-footer">
                    <span class="created-at">${formatDate(alert.created_at)}</span>
                </div>
            </div>
        `).join('');
        
        // 이벤트 리스너 다시 설정
        attachAlertEventListeners();
    }
    
    // 알림 이벤트 리스너 설정
    function attachNotificationEventListeners() {
        // 읽음 표시 버튼
        document.querySelectorAll('.mark-read').forEach(button => {
            button.addEventListener('click', function() {
                const card = this.closest('.notification-card');
                const notificationId = card.dataset.id;
                
                fetch(`/api/notifications/${notificationId}/mark-read`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        card.classList.remove('unread');
                        this.remove();
                        updateNotificationCount();
                    }
                })
                .catch(error => {
                    console.error('알림 읽음 처리 중 오류 발생:', error);
                    showToast('알림 읽음 처리 중 오류가 발생했습니다.', 'error');
                });
            });
        });
    }
    
    // 알림 이벤트 리스너 설정
    function attachAlertEventListeners() {
        // 삭제 버튼
        document.querySelectorAll('.delete-alert').forEach(button => {
            button.addEventListener('click', function() {
                const alertId = this.dataset.alertId;
                
                fetch(`/api/price-alerts/${alertId}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.closest('.alert-card').remove();
                        showToast('가격 알림이 삭제되었습니다.', 'success');
                    }
                })
                .catch(error => {
                    console.error('가격 알림 삭제 중 오류 발생:', error);
                    showToast('가격 알림 삭제 중 오류가 발생했습니다.', 'error');
                });
            });
        });
    }
    
    // 필터 이벤트 리스너
    const filterType = document.getElementById('filterType');
    if (filterType) {
        filterType.addEventListener('change', function() {
            const type = this.value;
            
            fetch(`/api/notifications?type=${type}`)
                .then(response => response.json())
                .then(data => {
                    updateNotificationsList(data);
                })
                .catch(error => {
                    console.error('알림 데이터 로드 중 오류 발생:', error);
                    showToast('알림 데이터 로드 중 오류가 발생했습니다.', 'error');
                });
        });
    }
    
    // 모두 읽음 표시 버튼
    const markAllRead = document.getElementById('markAllRead');
    if (markAllRead) {
        markAllRead.addEventListener('click', function() {
            fetch('/api/notifications/mark-all-read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.querySelectorAll('.notification-card.unread').forEach(card => {
                        card.classList.remove('unread');
                        const markReadBtn = card.querySelector('.mark-read');
                        if (markReadBtn) markReadBtn.remove();
                    });
                    updateNotificationCount();
                    showToast('모든 알림을 읽음 표시했습니다.', 'success');
                }
            })
            .catch(error => {
                console.error('알림 읽음 처리 중 오류 발생:', error);
                showToast('알림 읽음 처리 중 오류가 발생했습니다.', 'error');
            });
        });
    }
    
    // 가격 알림 설정 폼
    const priceAlertForm = document.getElementById('priceAlertForm');
    if (priceAlertForm) {
        priceAlertForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch('/api/price-alerts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    stock_code: formData.get('stockCode'),
                    condition: formData.get('condition'),
                    target_price: parseFloat(formData.get('targetPrice'))
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.reset();
                    fetch('/api/price-alerts')
                        .then(response => response.json())
                        .then(alerts => {
                            updateActiveAlerts(alerts);
                            showToast('가격 알림이 설정되었습니다.', 'success');
                        });
                } else {
                    showToast(data.message, 'error');
                }
            })
            .catch(error => {
                console.error('가격 알림 설정 중 오류 발생:', error);
                showToast('가격 알림 설정 중 오류가 발생했습니다.', 'error');
            });
        });
    }
    
    // 소켓 이벤트 리스너
    socket.on('notification', function(data) {
        // 새로운 알림이 도착하면 목록 업데이트
        fetch('/api/notifications')
            .then(response => response.json())
            .then(notifications => {
                updateNotificationsList(notifications);
                showToast(data.message, 'info');
            });
    });
    
    // 유틸리티 함수
    function getNotificationIcon(type) {
        switch (type) {
            case 'price_alert':
                return 'bell';
            case 'trade':
                return 'exchange-alt';
            default:
                return 'info-circle';
        }
    }
    
    function timeAgo(date) {
        const now = new Date();
        const past = new Date(date);
        const diff = now - past;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (minutes < 60) return `${minutes}분 전`;
        if (hours < 24) return `${hours}시간 전`;
        return `${days}일 전`;
    }
    
    function formatNumber(number) {
        return new Intl.NumberFormat('ko-KR').format(number);
    }
    
    function formatDate(date) {
        return new Date(date).toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // 애니메이션 효과
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        // 3초 후 제거
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
    
    // 초기화
    attachNotificationEventListeners();
    attachAlertEventListeners();
    updateNotificationCount();
}); 