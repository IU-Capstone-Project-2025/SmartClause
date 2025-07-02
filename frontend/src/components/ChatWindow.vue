<template>
  <div class="chat-container">
    <template v-if="space">
      <div class="chat-header">
        <h2>{{ space.name }}</h2>
        <p>{{ space.description }}</p>
      </div>
      <div class="chat-messages" ref="chatMessages">
        <div v-if="!messages.length && !isBotTyping" class="empty-state-chat">
          <p>No messages yet.</p>
          <span>Ask a question to start the conversation.</span>
        </div>
        <div v-else v-for="message in messages" :key="message.id" class="message" :class="message.sender">
          <div class="avatar">
            <svg v-if="message.sender === 'user'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
            <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>
          </div>
          <div class="message-content">
            <div class="message-bubble">
              <p>{{ message.text }}</p>
            </div>
            <span class="timestamp">{{ message.timestamp }}</span>
          </div>
        </div>
        <div v-if="isBotTyping" class="message bot">
          <div class="avatar">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>
          </div>
          <div class="message-content">
            <div class="message-bubble">
              <TypingIndicator />
            </div>
          </div>
        </div>
      </div>
      <div class="chat-input">
        <textarea
          ref="chatTextarea"
          v-model="newMessage"
          placeholder="Ask a question about the document..."
          rows="1"
          @input="adjustTextareaHeight"
          @keydown.enter.exact.prevent="sendMessage"
        ></textarea>
        <button @click="sendMessage" :disabled="!newMessage.trim()" title="Send message">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </div>
    </template>
    <div v-else class="empty-state-chat full-height">
      <p>Select a space</p>
      <span>or create a new one to begin.</span>
    </div>
  </div>
</template>

<script>
import TypingIndicator from '@/components/TypingIndicator.vue';

export default {
  name: 'ChatWindow',
  components: {
    TypingIndicator,
  },
  props: {
    space: {
      type: Object,
      default: null,
    },
    messages: {
      type: Array,
      required: true,
    },
    isBotTyping: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      newMessage: '',
    };
  },
  watch: {
    messages() {
      this.scrollToBottom();
    }
  },
  methods: {
    sendMessage() {
      if (this.newMessage.trim() !== '') {
        this.$emit('send-message', this.newMessage.trim());
        this.newMessage = '';
        this.$nextTick(() => {
          this.adjustTextareaHeight();
          this.scrollToBottom();
        });
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const chatMessages = this.$refs.chatMessages;
        if (chatMessages) {
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }
      });
    },
    adjustTextareaHeight() {
      this.$nextTick(() => {
        const textarea = this.$refs.chatTextarea;
        if (textarea) {
          textarea.style.height = 'auto';
          textarea.style.height = `${textarea.scrollHeight}px`;
        }
      });
    },
  },
}
</script>

<style scoped>
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  min-width: 0;
}

.chat-header {
  padding: 10px 80px;
  border-bottom: 1px solid #1e293b;
  flex-shrink: 0;
}

.chat-header h2 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 5px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 30px;
}

.message {
  margin-bottom: 25px;
  display: flex;
  align-items: flex-end;
  gap: 15px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  flex-shrink: 0;
}

.avatar svg {
  width: 22px;
  height: 22px;
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: 75%;
}

.message-bubble {
  padding: 15px 20px;
  border-radius: 18px;
  line-height: 1.6;
}

.message-bubble p {
  margin: 0;
}

.timestamp {
  font-size: 12px;
  color: #a0aec0;
  margin-top: 8px;
  padding: 0 5px;
}

/* User message styling */
.message.user {
  justify-content: flex-end;
}

.message.user .message-content {
  align-items: flex-end;
}

.message.user .message-bubble {
  background-color: #4a90e2;
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.message.user .avatar {
  order: 2;
  background-color: #357abd;
}

/* Bot message styling */
.message.bot .message-bubble {
  background-color: #1e293b;
  color: #cbd5e0;
  border-bottom-left-radius: 4px;
}

.message.bot .avatar {
  background-color: #2a3a50;
}

.chat-input {
  display: flex;
  margin: 20px;
  background-color: #1e293b;
  border-radius: 18px;
  padding: 8px;
  align-items: flex-end;
  flex-shrink: 0;
}

.chat-input textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: #ffffff;
  font-size: 16px;
  padding: 10px 15px;
  outline: none;
  resize: none;
  line-height: 1.5;
  max-height: 120px;
  overflow-y: auto;
  font-family: 'Inter', sans-serif;
  flex-direction: column;
  border-right: 1px solid #1e293b;
}

.chat-input textarea::placeholder {
    color: #a0aec0;
}

.chat-input button {
  background-color: #4a90e2;
  color: #ffffff;
  border: none;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s;
  flex-shrink: 0;
}

.chat-input button:hover {
  background-color: #357abd;
}

.chat-input button:disabled {
  background-color: #2a3a50;
  color: #6b7280;
  cursor: not-allowed;
}

.empty-state-chat {
  text-align: center;
  padding: 40px 20px;
  color: #a0aec0;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.empty-state-chat p {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 10px 0;
  color: #ffffff;
}
</style> 