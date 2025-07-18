<template>
  <div class="chat-screen">
    <button v-if="isSpacesSidebarCollapsed" @click="toggleSpacesSidebar" class="expand-btn left" :title="$t('chatScreen.openSidebar')">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.84l8.57 3.91a2 2 0 0 0 1.66 0l8.57-3.91a1 1 0 0 0 0-1.84Z"/><path d="m22 17.65-8.57 3.91a2 2 0 0 1-1.66 0L3.2 17.65"/><path d="m22 12.65-8.57 3.91a2 2 0 0 1-1.66 0L3.2 12.65"/></svg>
    </button>
     <button v-if="isDocumentsSidebarCollapsed && selectedSpaceId" @click="toggleDocumentsSidebar" class="expand-btn right upload-btn" :title="$t('chatScreen.openSidebar')">
       <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
       {{ $t('chatScreen.upload') }}
    </button>

    <SpacesSidebar 
      :spaces="spaces"
      :selected-space-id="selectedSpaceId"
      :is-collapsed="isSpacesSidebarCollapsed"
      @select-space="selectSpace"
      @create-space="handleCreateSpace"
      @delete-space="confirmDeleteSpace"
      @toggle-collapse="toggleSpacesSidebar"
      @update-space="handleUpdateSpace"
    />

    <ChatWindow
      :space="selectedSpace"
      :messages="messages"
      :is-bot-typing="isBotTyping"
      @send-message="sendMessage"
    />
    
    <DocumentsSidebar
      v-if="selectedSpaceId"
      ref="documentsSidebar"
      :space-id="selectedSpaceId"
      :documents="documents"
      :uploading-files="uploadingFiles[selectedSpaceId] || []"
      :is-collapsed="isDocumentsSidebarCollapsed"
      @upload-files="handleFileUpload"
      @toggle-collapse="toggleDocumentsSidebar"
      @delete-document="handleDeleteDocument"
    />
    
    <DuplicateDocumentModal
      v-if="duplicateModalData"
      :duplicate-info="duplicateModalData.duplicateInfo"
      @close="closeDuplicateModal"
      @reanalyze="handleReanalyze"
    />
  </div>
</template>

<script>
import SpacesSidebar from '@/components/SpacesSidebar.vue';
import DocumentsSidebar from '@/components/DocumentsSidebar.vue';
import ChatWindow from '@/components/ChatWindow.vue';
import DuplicateDocumentModal from '@/components/DuplicateDocumentModal.vue';
import * as api from '@/services/api';

export default {
  name: 'ChatScreen',
  components: {
    SpacesSidebar,
    DocumentsSidebar,
    ChatWindow,
    DuplicateDocumentModal,
  },
  data() {
    return {
      isBotTyping: false,
      isSpacesSidebarCollapsed: false,
      isDocumentsSidebarCollapsed: false,
      selectedSpaceId: null,
      spaces: [],
      messages: [],
      documents: [],
      uploadingFiles: {},
      duplicateModalData: null,
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
    async selectSpace(spaceId) {
      if (!spaceId) return;
      this.selectedSpaceId = spaceId;
      this.$router.replace({ name: 'Chat', params: { spaceId } });
      
      try {
        const spaceDetails = await api.getSpaceDetails(spaceId);
        if (spaceDetails.data.space) {
            const spaceIndex = this.spaces.findIndex(s => s.id === spaceId);
            if (spaceIndex !== -1) {
                this.spaces[spaceIndex] = spaceDetails.data.space;
            }
        }
      } catch (e) {
        console.error('Error fetching space details:', e);
      }

      try {
        const documentsRes = await api.getDocuments(spaceId);
        this.documents = documentsRes.data.documents || [];
      } catch (e) {
        console.error('Error fetching documents:', e);
        this.documents = [];
      }

      try {
        const messagesRes = await api.getMessages(spaceId);
        const sortedMessages = messagesRes.data.messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        this.messages = sortedMessages.map(m => ({
          id: m.id,
          sender: m.type === 'user' ? 'user' : 'bot',
          text: m.content,
          timestamp: new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }));
      } catch (e) {
        console.error('Error fetching messages:', e);
        this.messages = [];
      }
    },
    async sendMessage(messageText) {
      if (messageText.trim() === '') return;
      
      const tempId = Date.now();
      this.messages.push({
        id: tempId,
        sender: 'user',
        text: messageText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      });

      this.isBotTyping = true;
      try {
        await api.sendMessage(this.selectedSpaceId, { content: messageText, type: 'user' });
        // After sending, refetch messages to get the bot's response
        const messagesRes = await api.getMessages(this.selectedSpaceId);
        const sortedMessages = messagesRes.data.messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        this.messages = sortedMessages.map(m => ({
          id: m.id,
          sender: m.type === 'user' ? 'user' : 'bot',
          text: m.content,
          timestamp: new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }));
      } catch (error) {
        console.error('Error sending message:', error);
        this.messages = this.messages.filter(m => m.id !== tempId);
      } finally {
        this.isBotTyping = false;
      }
    },
    async confirmDeleteSpace(deletedSpaceId) {
        try {
            await api.deleteSpace(deletedSpaceId);
            this.spaces = this.spaces.filter(s => s.id !== deletedSpaceId);

            if (this.selectedSpaceId === deletedSpaceId) {
                if (this.spaces.length > 0) {
                    this.selectSpace(this.spaces[0].id);
                } else {
                    this.selectedSpaceId = null;
                    this.documents = [];
                    this.messages = [];
                }
            }
        } catch (error) {
            console.error('Error deleting space:', error);
        }
    },
    async handleCreateSpace(spaceName) {
      try {
        const response = await api.createSpace({ name: spaceName, description: '' });
        const newSpace = response.data.space;
        this.spaces.push(newSpace);
        this.selectSpace(newSpace.id);
      } catch (error) {
        console.error('Error creating space:', error);
      }
    },
    async handleUpdateSpace(updatedSpace) {
      try {
        const response = await api.updateSpace(updatedSpace.id, { name: updatedSpace.name });
        const returnedSpace = response.data.space;
        const index = this.spaces.findIndex(s => s.id === returnedSpace.id);
        if (index !== -1) {
          this.spaces.splice(index, 1, returnedSpace);
        }
      } catch (error) {
        console.error('Error updating space:', error);
      }
    },
    async handleFileUpload(files) {
        if (!files.length || !this.selectedSpaceId) return;
        
        const currentSpaceId = this.selectedSpaceId;

        // Process files one by one to handle duplicates individually
        for (const file of files) {
            await this.handleSingleFileUpload(file, currentSpaceId);
        }
    },
    
    async handleSingleFileUpload(file, spaceId) {
        const uploadingFile = {
            id: `uploading-${file.name}-${Date.now()}`,
            name: file.name,
        };
        
        // Add to uploading files list
        this.uploadingFiles = {
          ...this.uploadingFiles,
          [spaceId]: [...(this.uploadingFiles[spaceId] || []), uploadingFile]
        };

        try {
            const result = await api.uploadDocumentWithDuplicateCheck(spaceId, file);
            
            if (result.isDuplicate) {
                // Show duplicate modal
                this.duplicateModalData = {
                    duplicateInfo: result.duplicateInfo,
                    file: file,
                    spaceId: spaceId,
                    uploadingFile: uploadingFile
                };
            } else if (result.success) {
                // Successful upload - refresh documents list
                if (this.selectedSpaceId === spaceId) {
                    await this.refreshDocuments(spaceId);
                }
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            if (this.$refs.documentsSidebar) {
              const message = error.response?.data?.error || this.$t('documentsSidebar.uploadError');
              this.$refs.documentsSidebar.uploadError = message;
            }
        } finally {
            // Remove from uploading files list
            if (this.uploadingFiles[spaceId]) {
                this.uploadingFiles = {
                  ...this.uploadingFiles,
                  [spaceId]: this.uploadingFiles[spaceId].filter(f => f.id !== uploadingFile.id)
                };
            }
        }
    },
    
    async refreshDocuments(spaceId) {
        try {
            const documentsRes = await api.getDocuments(spaceId);
            this.documents = documentsRes.data.documents || [];
        } catch (e) {
            console.error('Error fetching documents after upload:', e);
        }
    },
    
    closeDuplicateModal() {
        this.duplicateModalData = null;
    },
    
    async handleReanalyze() {
        if (!this.duplicateModalData) return;
        
        const existingDocumentId = this.duplicateModalData.duplicateInfo.existingDocumentId;
        const spaceId = this.duplicateModalData.spaceId;
        
        // Close modal immediately
        this.closeDuplicateModal();
        
        // Add document to reanalyzing state if documents sidebar exists
        if (this.$refs.documentsSidebar) {
            this.$refs.documentsSidebar.reanalyzingDocIds.push(existingDocumentId);
        }
        
        try {
            await api.reanalyzeDocument(existingDocumentId);
            
            // Poll until analysis is complete, then navigate
            await this.waitForAnalysisCompletion(existingDocumentId);
            
            // Navigate to analysis page only when results are ready
            this.$router.push({
                name: 'Analysis',
                params: {
                    spaceId: spaceId,
                    documentId: existingDocumentId
                }
            }).then(() => {
                // Remove from reanalyzing list when navigation is complete
                if (this.$refs.documentsSidebar) {
                    const index = this.$refs.documentsSidebar.reanalyzingDocIds.indexOf(existingDocumentId);
                    if (index > -1) {
                        this.$refs.documentsSidebar.reanalyzingDocIds.splice(index, 1);
                    }
                }
            });
        } catch (error) {
            console.error('Error reanalyzing document:', error);
            if (this.$refs.documentsSidebar) {
                const message = error.response?.data?.error || this.$t('documentsSidebar.reanalysisError');
                this.$refs.documentsSidebar.uploadError = message;
                // Remove from reanalyzing list on error
                const index = this.$refs.documentsSidebar.reanalyzingDocIds.indexOf(existingDocumentId);
                if (index > -1) {
                    this.$refs.documentsSidebar.reanalyzingDocIds.splice(index, 1);
                }
            }
        }
    },
    
    async waitForAnalysisCompletion(documentId) {
      const maxAttempts = 120; // 10 minutes (120 * 5 seconds)
      let attempts = 0;
      
      return new Promise((resolve, reject) => {
        const poll = async () => {
          attempts++;
          
          try {
            const response = await api.getDocumentAnalysis(documentId);
            
            // Check if analysis is complete (document_points exists, even if empty)
            if (response.data && response.data.document_points !== undefined) {
              // Analysis is complete (even if no issues found)
              resolve();
              return;
            }
            
            if (attempts >= maxAttempts) {
              reject(new Error('Analysis timeout - took too long to complete'));
              return;
            }
            
            // Continue polling
            setTimeout(poll, 5000); // Poll every 5 seconds
            
          } catch (error) {
            // 404 or other error means analysis not ready yet
            if (attempts >= maxAttempts) {
              reject(error);
              return;
            }
            
            // Continue polling on error (analysis might not be ready yet)
            setTimeout(poll, 5000);
          }
        };
        
        // Start polling
        poll();
      });
    },
    async handleDeleteDocument(docId) {
      try {
        await api.deleteDocument(docId);
        this.documents = this.documents.filter(d => d.id !== docId);
      } catch (error) {
        console.error('Error deleting document:', error);
      }
    },
    async fetchSpaces() {
        try {
            const response = await api.getSpaces();
            this.spaces = response.data.spaces || [];
            
            const spaceIdFromRoute = this.$route.params.spaceId;
            if (spaceIdFromRoute && this.spaces.some(s => s.id === spaceIdFromRoute)) {
                this.selectSpace(spaceIdFromRoute);
            } else if (this.spaces.length > 0) {
                this.selectSpace(this.spaces[0].id);
            }
        } catch (error) {
            console.error('Error fetching spaces:', error);
            if (error.response && error.response.status === 401) {
              this.$router.push('/login');
            }
        }
    }
  },
  created() {
    this.fetchSpaces();
  },
  watch: {
    '$route.params.spaceId'(newSpaceId) {
      if (newSpaceId && newSpaceId !== this.selectedSpaceId) {
        this.selectSpace(newSpaceId);
      }
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