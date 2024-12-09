import { socket } from './common/socket.js';

document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    
    let isProcessing = false;

    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message || isProcessing) return;
        
        // 사용자 메시지 추가
        addMessage(message, 'user');
        messageInput.value = '';
        
        isProcessing = true;
        
        try {
            // 서버에 메시지 전송
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            // 봇 응답 추가
            addMessage(data.response, 'bot');
        } catch (error) {
            console.error('Error:', error);
            addMessage('죄송합니다. 오류가 발생했습니다.', 'bot');
        } finally {
            isProcessing = false;
        }
    });

    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${text}</p>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});

function sendChatMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (message) {
        appendChatMessage(message, 'user');
        socket.emit('chat_message', { message });
        messageInput.value = '';
    }
}

function appendChatMessage(message, sender) {
    const chatBox = document.getElementById('chatBox');
    if (!chatBox) return;

    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${sender}`;
    messageElement.textContent = message;
    chatBox.appendChild(messageElement);

    chatBox.scrollTop = chatBox.scrollHeight;
} 