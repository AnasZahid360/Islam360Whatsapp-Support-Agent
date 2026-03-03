/**
 * MakTek Support Chatbot - Frontend Logic
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

class ChatApp {
    constructor() {
        this.messagesContainer = document.getElementById('chat-messages');
        this.chatForm = document.getElementById('chat-form');
        this.userInput = document.getElementById('user-input');
        this.ticketList = document.getElementById('ticket-list');
        this.displayUserId = document.getElementById('display-user-id');
        this.chatWindow = document.getElementById('chat-window');

        this.userId = this.getOrGenerateId('maktek_user_id', 'user_');
        this.threadId = this.getOrGenerateId('maktek_thread_id', 'thread_' + Date.now() + '_');

        this.init();
    }

    getOrGenerateId(key, prefix) {
        let id = localStorage.getItem(key);
        if (!id) {
            id = prefix + Math.random().toString(36).substring(2, 9);
            localStorage.setItem(key, id);
        }
        return id;
    }

    init() {
        this.displayUserId.textContent = this.userId;
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));

        // Initial welcome message
        setTimeout(() => {
            this.addMessage("Hello! I'm your MakTek Support Assistant. How can I help you today?", 'ai');
        }, 1000);
    }

    async handleSubmit(e) {
        e.preventDefault();
        const text = this.userInput.value.trim();
        if (!text) return;

        this.userInput.value = '';
        this.addMessage(text, 'user');

        const typingId = this.addTypingIndicator();

        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    user_id: this.userId,
                    thread_id: this.threadId
                })
            });

            if (!response.ok) throw new Error('API request failed');

            const data = await response.json();
            this.removeTypingIndicator(typingId);
            this.addMessage(data.response, 'ai');

            // Handle tickets if present in docs or response text
            this.scanForTickets(data.response, data.docs);

        } catch (error) {
            console.error('Chat error:', error);
            this.removeTypingIndicator(typingId);
            this.addMessage("I'm sorry, I'm having trouble connecting to the support system. Please ensure the backend is running and refresh.", 'ai');
        }
    }

    addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;

        // Simple markdown-ish bolding
        const formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');

        msgDiv.innerHTML = formattedText;
        this.messagesContainer.appendChild(msgDiv);
        this.scrollToBottom();
    }

    addTypingIndicator() {
        const id = 'typing-' + Date.now();
        const indicator = document.createElement('div');
        indicator.id = id;
        indicator.className = 'message ai typing-indicator';
        indicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        this.messagesContainer.appendChild(indicator);
        this.scrollToBottom();
        return id;
    }

    removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    scrollToBottom() {
        // Use a slight delay to ensure the DOM has updated and element heights are correct
        setTimeout(() => {
            this.chatWindow.scrollTo({
                top: this.chatWindow.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
    }

    scanForTickets(responseText, docs) {
        // Regex to find ticket IDs like TKT-20260218110353-test_use
        const ticketRegex = /TKT-[0-9a-fA-Z-]+/g;
        const matches = responseText.match(ticketRegex);

        if (matches) {
            matches.forEach(ticketId => {
                this.addTicketToSidebar(ticketId);
            });
        }
    }

    addTicketToSidebar(ticketId) {
        // Prevent duplicates
        if (document.getElementById(`ticket-${ticketId}`)) return;

        if (this.ticketList.querySelector('.no-tickets')) {
            this.ticketList.innerHTML = '';
        }

        const ticketCard = document.createElement('div');
        ticketCard.id = `ticket-${ticketId}`;
        ticketCard.className = 'ticket-card';
        ticketCard.innerHTML = `
            <div class="ticket-id">${ticketId}</div>
            <div style="font-size: 13px; margin-top: 5px;">Status: <span style="color: #00e676">Open</span></div>
        `;
        this.ticketList.prepend(ticketCard);
    }
}

// Start the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
