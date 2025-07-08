<template>
  <div class="chat-screen">
    <button v-if="isSpacesSidebarCollapsed" @click="toggleSpacesSidebar" class="expand-btn left" title="Open sidebar">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.84l8.57 3.91a2 2 0 0 0 1.66 0l8.57-3.91a1 1 0 0 0 0-1.84Z"/><path d="m22 17.65-8.57 3.91a2 2 0 0 1-1.66 0L3.2 17.65"/><path d="m22 12.65-8.57 3.91a2 2 0 0 1-1.66 0L3.2 12.65"/></svg>
    </button>
     <button v-if="isDocumentsSidebarCollapsed" @click="toggleDocumentsSidebar" class="expand-btn right upload-btn" title="Open sidebar">
       <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
       Upload
    </button>

    <SpacesSidebar 
      :spaces="spaces"
      :selected-space-id="selectedSpaceId"
      :is-collapsed="isSpacesSidebarCollapsed"
      @select-space="selectSpace"
      @create-space="handleCreateSpace"
      @delete-space="confirmDeleteSpace"
      @toggle-collapse="toggleSpacesSidebar"
    />

    <ChatWindow
      :space="selectedSpace"
      :messages="messages"
      :is-bot-typing="isBotTyping"
      @send-message="sendMessage"
    />
    
    <DocumentsSidebar
      :documents="documents"
      :is-collapsed="isDocumentsSidebarCollapsed"
      @upload-files="handleFileUpload"
      @toggle-collapse="toggleDocumentsSidebar"
      @delete-document="handleDeleteDocument"
      @analyze-document="handleAnalyzeDocument"
    />
  </div>
</template>

<script>
import SpacesSidebar from '@/components/SpacesSidebar.vue';
import DocumentsSidebar from '@/components/DocumentsSidebar.vue';
import ChatWindow from '@/components/ChatWindow.vue';

export default {
  name: 'ChatScreen',
  components: {
    SpacesSidebar,
    DocumentsSidebar,
    ChatWindow,
  },
  data() {
    return {
      isBotTyping: false,
      isSpacesSidebarCollapsed: false,
      isDocumentsSidebarCollapsed: false,
      selectedSpaceId: 1,
      spaces: [
        { id: 1, name: 'Contract Analysis', description: 'Discussion about the main contract.' },
        { id: 2, name: 'Financial Projections', description: 'Planning for Q3 financials.' },
        { id: 3, name: 'Marketing Strategy', description: 'Brainstorming for the new campaign.' },
      ],
      messages: [
        { id: 1, sender: 'user', text: 'What are the key risks identified in the contract?', timestamp: '10:30 AM' },
        { id: 2, sender: 'bot', text: 'The key risks are related to termination clauses and liability limitations. Would you like a detailed summary?', timestamp: '10:31 AM' },
      ],
      documents: [
        { id: 1, name: 'Main_Contract_v2.docx' },
        { id: 2, name: 'Appendix_A.pdf' },
      ],
    };
  },
  computed: {
    selectedSpace() {
      return this.spaces.find(space => space.id === this.selectedSpaceId);
    }
  },
  methods: {
    toggleSpacesSidebar() {
      this.isSpacesSidebarCollapsed = !this.isSpacesSidebarCollapsed;
    },
    toggleDocumentsSidebar() {
      this.isDocumentsSidebarCollapsed = !this.isDocumentsSidebarCollapsed;
    },
    selectSpace(spaceId) {
      this.selectedSpaceId = spaceId;
      // Here you would typically fetch data for the selected space
    },
    sendMessage(messageText) {
      if (messageText.trim() !== '') {
        this.messages.push({
          id: Date.now(),
          sender: 'user',
          text: messageText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        });
        this.isBotTyping = true;
        
        setTimeout(() => {
          this.isBotTyping = false;
          this.messages.push({
            id: Date.now(),
            sender: 'bot',
            text: 'I am processing your request... Please wait.',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          });
        }, 2000);
      }
    },
    confirmDeleteSpace(deletedSpaceId) {
      this.spaces = this.spaces.filter(s => s.id !== deletedSpaceId);

      if (this.selectedSpaceId === deletedSpaceId) {
        if (this.spaces.length > 0) {
          this.selectedSpaceId = this.spaces[0].id;
        } else {
          this.selectedSpaceId = null;
        }
      }
    },
    handleCreateSpace(spaceName) {
      const newSpace = {
        id: Date.now(),
        name: spaceName,
        description: 'A new space for collaboration.'
      };
      this.spaces.push(newSpace);
      this.selectSpace(newSpace.id);
    },
    handleFileUpload(files) {
        if (!files.length) return;
        
        for(let i=0; i< files.length; i++) {
            const newDoc = {
                id: Date.now() + i,
                name: files[i].name
            };
            this.documents.push(newDoc);
        }
    },
    handleDeleteDocument(docId) {
      this.documents = this.documents.filter(d => d.id !== docId);
    },
    handleAnalyzeDocument(doc) {
      const mockResults = {
        document_points: [
          {
            point_number: 1,
            point_content: "This is a mock analysis point for " + doc.name,
            analysis_points: [
              { cause: 'Mock Cause', risk: 'Высокий', recommendation: 'Mock Recommendation' },
              { cause: 'Another Mock Cause', risk: 'Средний', recommendation: 'Another Mock Recommendation' }
            ]
          },
          {
            point_number: 2,
            point_content: "This is another mock analysis point.",
            analysis_points: [
              { cause: 'Third Mock Cause', risk: 'Низкий', recommendation: 'Third Mock Recommendation' }
            ]
          }
        ]
      };
      
      sessionStorage.setItem('analysisResults', JSON.stringify(mockResults));
      this.$router.push({ path: '/results', query: { fileName: doc.name } });
    }
  },
  created() {
    const spaceId = parseInt(this.$route.params.spaceId);
    if (spaceId && this.spaces.some(s => s.id === spaceId)) {
        this.selectedSpaceId = spaceId;
    } else if (this.spaces.length > 0) {
        this.selectedSpaceId = this.spaces[0].id;
    } else {
        this.selectedSpaceId = null;
    }
  }
};
</script>

<style scoped>
.chat-screen {
  display: flex;
  height: 100vh;
  background-color: #0c1a2e;
  color: #ffffff;
  font-family: 'Inter', sans-serif;
  overflow: hidden;
  position: relative;
}

.expand-btn {
  position: absolute;
  top: 28px;
  background-color: transparent;
  border: none;
  color: #a0aec0;
  cursor: pointer;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.expand-btn.left {
  left: 20px;
  background-color: transparent;
  color: #a0aec0;
  border: 1px solid #a0aec0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.expand-btn.left:hover {
  background-color: #1e293b;
  color: #ffffff;
}

.expand-btn.left .logo {
    color: #4a90e2;
}

.expand-btn.right {
  right: 30px;
  top: 20px;
}

.expand-btn.upload-btn {
    background-color: #38a169;
    color: #ffffff;
    padding: 8px 15px;
    border-radius: 8px;
    font-weight: 600;
    gap: 8px;
}

.expand-btn.upload-btn:hover {
    background-color: #2f855a;
}
</style> 

.expand-btn.left:hover {
  background-color: #1e293b;
  color: #ffffff;
}