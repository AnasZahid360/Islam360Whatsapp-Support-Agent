/**
 * MakTek Support Chatbot - Frontend Logic
 * Supports both text chat and voice messages.
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
        this.micBtn = document.getElementById('mic-btn');
        this.voiceStatus = document.getElementById('voice-status');
        this.voiceStatusText = document.getElementById('voice-status-text');

        this.userId = this.getOrGenerateId('maktek_user_id', 'user_');
        this.threadId = this.getOrGenerateId('maktek_thread_id', 'thread_' + Date.now() + '_');

        // Voice recording state
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.recordingTimer = null;
        this.recordingSeconds = 0;

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

        // Voice recording — click to toggle
        this.micBtn.addEventListener('click', () => this.toggleRecording());

        // Initial welcome message
        setTimeout(() => {
            this.addMessage("Hello! I'm your MakTek Support Assistant. How can I help you today? You can type or tap the 🎙️ mic button to ask with your voice.", 'ai');
        }, 1000);
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
                    thread_id: this.threadId
                })
            });

            if (!response.ok) throw new Error('API request failed');

            const data = await response.json();
            this.removeTypingIndicator(typingId);
            this.addMessage(data.response, 'ai');

            this.scanForTickets(data.response, data.docs);

        } catch (error) {
            console.error('Chat error:', error);
            this.removeTypingIndicator(typingId);
            this.addMessage("I'm sorry, I'm having trouble connecting to the support system. Please ensure the backend is running and refresh.", 'ai');
        }
    }

    // ─── Voice Recording ─────────────────────────────────────

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            this.audioChunks = [];
            this.mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

            this.mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    this.audioChunks.push(e.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                // Stop all tracks to release the microphone
                stream.getTracks().forEach(track => track.stop());
                this.handleRecordingComplete();
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.recordingSeconds = 0;

            // UI updates
            this.micBtn.classList.add('recording');
            this.voiceStatus.style.display = 'flex';
            this.voiceStatusText.textContent = 'Recording... 0s';

            // Timer
            this.recordingTimer = setInterval(() => {
                this.recordingSeconds++;
                this.voiceStatusText.textContent = `Recording... ${this.recordingSeconds}s`;

                // Auto-stop after 60 seconds
                if (this.recordingSeconds >= 60) {
                    this.stopRecording();
                }
            }, 1000);

        } catch (err) {
            console.error('Microphone access error:', err);
            this.addMessage('⚠️ Could not access microphone. Please allow microphone permissions and try again.', 'ai');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }

        this.isRecording = false;
        this.micBtn.classList.remove('recording');

        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
    }

    async handleRecordingComplete() {
        if (this.audioChunks.length === 0) {
            this.voiceStatus.style.display = 'none';
            return;
        }

        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });

        // Show user that voice message was sent
        this.addMessage(`🎙️ Voice message (${this.recordingSeconds}s)`, 'user');

        // Update status
        this.voiceStatusText.textContent = 'Transcribing...';

        const typingId = this.addTypingIndicator();

        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'voice_message.webm');
            formData.append('user_id', this.userId);
            formData.append('thread_id', this.threadId);

            const response = await fetch(`${API_BASE_URL}/voice-chat`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || 'Voice chat request failed');
            }

            const data = await response.json();
            this.removeTypingIndicator(typingId);
            this.voiceStatus.style.display = 'none';

            // Show transcription as a subtle note
            if (data.transcription) {
                this.addTranscriptionNote(data.transcription, data.language_detected);
            }

            // Show the chatbot response
            this.addMessage(data.response, 'ai');

            this.scanForTickets(data.response);

        } catch (error) {
            console.error('Voice chat error:', error);
            this.removeTypingIndicator(typingId);
            this.voiceStatus.style.display = 'none';
            this.addMessage(`⚠️ Voice processing failed: ${error.message}. Please try again or type your question.`, 'ai');
        }
    }

    addTranscriptionNote(text, lang) {
        const noteDiv = document.createElement('div');
        noteDiv.className = 'transcription-note';
        noteDiv.innerHTML = `<span class="transcription-label">📝 Heard:</span> "${text}" <span class="transcription-lang">(${lang})</span>`;
        this.messagesContainer.appendChild(noteDiv);
        this.scrollToBottom();
    }

    // ─── Shared UI Helpers ───────────────────────────────────

    addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;

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
        setTimeout(() => {
            this.chatWindow.scrollTo({
                top: this.chatWindow.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
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
