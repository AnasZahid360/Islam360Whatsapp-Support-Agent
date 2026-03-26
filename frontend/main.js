/**
 * MakTek Support Chatbot - Frontend Logic
 * Supports both text chat and voice messages.
 */

import LiveKitVoiceManager from './livekit-integration.js';

const API_BASE_URL = 'http://localhost:8000';

class ChatApp {
    constructor() {
        this.messagesContainer = document.getElementById('chat-messages');
        this.chatForm = document.getElementById('chat-form');
        this.userInput = document.getElementById('user-input');
        this.ticketList = document.getElementById('ticket-list');
        this.displayUserId = document.getElementById('display-user-id');
        this.chatWindow = document.getElementById('chat-window');
        this.micBtn = document.getElementById('mic-btn');
        this.newChatBtn = document.getElementById('new-chat-btn');
        this.voiceStatus = document.getElementById('voice-status');
        this.voiceStatusText = document.getElementById('voice-status-text');

        this.userId = this.getOrGenerateId('maktek_user_id', 'user_');
        this.threadId = this.getOrGenerateId('maktek_thread_id', 'thread_' + Date.now() + '_');

        // Voice recording state
        this.voiceManager = new LiveKitVoiceManager();
        this.voiceConnected = false;
        this.lastVoiceErrorMessage = '';
        this.startFreshOnReload = true;

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

    async init() {
        this.displayUserId.textContent = this.userId;
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));

        // Voice — click to connect/disconnect LiveKit room
        this.micBtn.addEventListener('click', () => this.toggleRecording());
        this.newChatBtn?.addEventListener('click', () => this.startNewChat());

        // Start a fresh thread on every page load
        if (this.startFreshOnReload) {
            await this.startNewChat();
            return;
        }

        // Restore persistent state from server
        await this.restoreSessionState();
    }

    // ─── Persistent State Restoration ────────────────────────

    async restoreSessionState(allowLatestThreadRecovery = true) {
        try {
            const response = await fetch(`${API_BASE_URL}/init-session/${this.userId}/${this.threadId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                console.warn('Could not restore session state');
                this.showInitialWelcome();
                return;
            }

            const data = await response.json();

            // Restore chat history
            if (data.chat_history && data.chat_history.length > 0) {
                for (const msg of data.chat_history) {
                    const sender = msg.role === 'assistant' ? 'ai' : msg.role;
                    this.addMessage(msg.content, sender, false);
                }
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            } else {
                const recovered = allowLatestThreadRecovery
                    ? await this.restoreFromLatestThread()
                    : false;
                if (!recovered) {
                    this.showInitialWelcome();
                }
            }

            // Restore tickets
            if (data.tickets && data.tickets.length > 0) {
                this.renderTickets(data.tickets);
            }

            console.log(`✓ Restored ${data.chat_history?.length || 0} messages and ${data.tickets?.length || 0} tickets`);

        } catch (error) {
            console.error('Error restoring session:', error);
            this.showInitialWelcome();
        }
    }

    async startNewChat() {
        if (this.voiceConnected) {
            try {
                await this.voiceManager.disconnect();
            } catch (error) {
                console.error('Error disconnecting voice during new chat:', error);
            }
            this.voiceConnected = false;
            this.micBtn.classList.remove('recording');
            this.voiceStatus.style.display = 'none';
        }

        this.threadId = `thread_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
        localStorage.setItem('maktek_thread_id', this.threadId);

        this.messagesContainer.innerHTML = '';
        this.lastVoiceErrorMessage = '';

        if (this.ticketList) {
            this.ticketList.innerHTML = '<p class="no-tickets">No active tickets.</p>';
        }

        await this.restoreSessionState(false);
    }

    async restoreFromLatestThread() {
        try {
            const sessionsResponse = await fetch(`${API_BASE_URL}/user-sessions/${this.userId}`);
            if (!sessionsResponse.ok) return false;

            const sessionsData = await sessionsResponse.json();
            if (!sessionsData.sessions || sessionsData.sessions.length === 0) return false;

            const sortedSessions = [...sessionsData.sessions].sort((a, b) => {
                return new Date(b.last_updated).getTime() - new Date(a.last_updated).getTime();
            });

            for (const session of sortedSessions) {
                const historyResponse = await fetch(`${API_BASE_URL}/chat-history/${this.userId}/${session.thread_id}`);
                if (!historyResponse.ok) continue;

                const historyData = await historyResponse.json();
                if (!historyData.messages || historyData.messages.length === 0) continue;

                this.threadId = session.thread_id;
                localStorage.setItem('maktek_thread_id', this.threadId);

                for (const msg of historyData.messages) {
                    const sender = msg.role === 'assistant' ? 'ai' : msg.role;
                    this.addMessage(msg.content, sender, false);
                }

                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
                console.log(`✓ Recovered history from latest thread: ${this.threadId}`);
                return true;
            }

            return false;
        } catch (error) {
            console.error('Failed latest-thread recovery:', error);
            return false;
        }
    }

    showInitialWelcome() {
        // Clear existing messages if any
        if (this.messagesContainer.children.length === 0) {
            setTimeout(() => {
                this.addMessage("Hello! I'm your MakTek Support Assistant. How can I help you today? You can type or tap the 🎙️ mic button to ask with your voice.", 'ai');
            }, 500);
        }
    }

    renderTickets(tickets) {
        if (!this.ticketList) return;

        this.ticketList.innerHTML = '';

        if (tickets.length === 0) {
            this.ticketList.innerHTML = '<p style="text-align: center; color: #999;">No support tickets yet</p>';
            return;
        }

        tickets.forEach(ticket => {
            const ticketEl = document.createElement('div');
            ticketEl.className = `ticket-item status-${ticket.status}`;
            ticketEl.innerHTML = `
                <div class="ticket-header">
                    <span class="ticket-id">${ticket.ticket_id}</span>
                    <span class="ticket-status">${ticket.status.toUpperCase()}</span>
                </div>
                <div class="ticket-body">
                    <p><strong>Issue:</strong> ${ticket.issue}</p>
                    <p><strong>Priority:</strong> <span class="priority-${ticket.priority}">${ticket.priority}</span></p>
                    <p><strong>Created:</strong> ${new Date(ticket.created_at).toLocaleString()}</p>
                </div>
            `;
            this.ticketList.appendChild(ticketEl);
        });
    }

    // ─── Text Chat ───────────────────────────────────────────

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
                    thread_id: this.threadId,
                    return_tts: true
                })
            });

            if (!response.ok) throw new Error('API request failed');

            const data = await response.json();
            this.removeTypingIndicator(typingId);
            this.addMessage(data.response, 'ai');

            if (data.tts_audio_base64) {
                this.playAssistantAudio(data.tts_audio_base64, data.tts_audio_mime_type || 'audio/mpeg');
            }

            this.scanForTickets(data.response, data.docs);
            await this.refreshTickets();

        } catch (error) {
            console.error('Chat error:', error);
            this.removeTypingIndicator(typingId);
            this.addMessage("I'm sorry, I'm having trouble connecting to the support system. Please ensure the backend is running and refresh.", 'ai');
        }
    }

    // ─── Voice Recording ─────────────────────────────────────

    async toggleRecording() {
        if (this.voiceConnected) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            this.voiceStatus.style.display = 'flex';
            this.voiceStatusText.textContent = 'Connecting voice...';

            await this.voiceManager.connectToVoiceRoom(this.userId, 'support-agent');

            this.voiceConnected = true;
            this.micBtn.classList.add('recording');
            this.voiceStatusText.textContent = 'Voice connected • Speak now';
            this.lastVoiceErrorMessage = '';
            this.addMessage('🎙️ Voice connected. You can speak naturally now.', 'ai');

        } catch (err) {
            console.error('Microphone access error:', err);
            this.voiceStatus.style.display = 'none';

            const rawError = (err && err.message) ? err.message : 'Unable to join LiveKit room';
            const lowerError = rawError.toLowerCase();
            let uiError = `⚠️ Voice connection failed: ${rawError}.`;

            if (lowerError.includes('signal connection') || lowerError.includes('failed to fetch')) {
                uiError = '⚠️ Live voice is unavailable right now because the LiveKit server is not reachable at ws://localhost:7880. Text chat still works.';
            }

            if (this.lastVoiceErrorMessage !== uiError) {
                this.addMessage(uiError, 'ai');
                this.lastVoiceErrorMessage = uiError;
            }
        }
    }

    async stopRecording() {
        try {
            await this.voiceManager.disconnect();
        } catch (error) {
            console.error('Voice disconnect error:', error);
        }

        this.voiceConnected = false;
        this.micBtn.classList.remove('recording');
        this.voiceStatus.style.display = 'none';
        this.addMessage('🔇 Voice disconnected.', 'ai');
    }

    async handleRecordingComplete() {
        return;
    }

    addTranscriptionNote(text, lang) {
        const noteDiv = document.createElement('div');
        noteDiv.className = 'transcription-note';
        noteDiv.innerHTML = `<span class="transcription-label">📝 Heard:</span> "${text}" <span class="transcription-lang">(${lang})</span>`;
        this.messagesContainer.appendChild(noteDiv);
        this.scrollToBottom();
    }

    playAssistantAudio(base64Audio, mimeType = 'audio/mpeg') {
        try {
            const audio = new Audio(`data:${mimeType};base64,${base64Audio}`);
            audio.play().catch((error) => {
                console.warn('Autoplay blocked or failed:', error);
            });
        } catch (error) {
            console.error('Failed to play assistant audio:', error);
        }
    }

    // ─── Shared UI Helpers ───────────────────────────────────

    addMessage(text, sender, autoScroll = true) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;

        const formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');

        msgDiv.innerHTML = formattedText;
        this.messagesContainer.appendChild(msgDiv);
        
        if (autoScroll) {
            this.scrollToBottom();
        }
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
        setTimeout(() => {
            this.chatWindow.scrollTo({
                top: this.chatWindow.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
    }

    async refreshTickets() {
        try {
            const res = await fetch(`${API_BASE_URL}/user-tickets/${this.userId}`);
            if (!res.ok) return;
            const data = await res.json();
            if (data.tickets && data.tickets.length > 0) {
                this.renderTickets(data.tickets);
            }
        } catch (e) {
            // silently ignore — tickets will still show via scanForTickets
        }
    }

    scanForTickets(responseText, docs) {
        const ticketRegex = /TKT-[0-9a-fA-Z-]+/g;
        const matches = responseText.match(ticketRegex);

        if (matches) {
            matches.forEach(ticketId => {
                this.addTicketToSidebar(ticketId);
            });
        }
    }

    addTicketToSidebar(ticketId) {
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
