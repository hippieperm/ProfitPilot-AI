// Toast 클래스가 이미 존재하는지 확인
if (!window.hasOwnProperty('Toast')) {
    class Toast {
        constructor() {
            // DOM이 로드된 후에 컨테이너 생성
            if (document.body) {
                this.container = this.createContainer();
            } else {
                document.addEventListener('DOMContentLoaded', () => {
                    this.container = this.createContainer();
                });
            }
        }

        createContainer() {
            const container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
            return container;
        }

        show(message, type = 'success') {
            if (!this.container) {
                this.container = this.createContainer();
            }

            const toast = document.createElement('div');
            toast.className = `toast-notification ${type}`;
            
            // 아이콘 선택
            const icon = type === 'success' ? '✓' : '✕';
            
            toast.innerHTML = `
                <div class="toast-icon">${icon}</div>
                <div class="toast-content">${message}</div>
            `;

            // 토스트를 컨테이너에 추가
            this.container.appendChild(toast);

            // 클릭으로 닫기
            toast.addEventListener('click', () => this.hide(toast));

            // 3초 후 자동으로 닫기
            setTimeout(() => this.hide(toast), 3000);
        }

        hide(toast) {
            toast.classList.add('hide');
            toast.addEventListener('animationend', () => {
                toast.remove();
            });
        }
    }

    // 전역 Toast 인스턴스 생성
    window.Toast = new Toast();
} 