<template>
  <div class="documents-sidebar" :class="{ 'collapsed': isCollapsed }">
    <DeleteDocumentModal
      v-if="isDeleteModalOpen"
      :document="docToDelete"
      @close="cancelDelete"
      @confirm="confirmDelete"
    />
    <div class="sidebar-content">
      <div class="documents-header">
        <h3>Documents</h3>
        <button @click="$emit('toggle-collapse')" class="sidebar-toggle-btn" title="Collapse sidebar">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="15" y1="3" x2="15" y2="21"></line></svg>
        </button>
        <button class="upload-btn" @click="triggerFileUpload">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
          <span>Upload</span>
        </button>
        <input type="file" ref="fileInput" @change="handleFileUpload" style="display: none;" multiple>
      </div>
      <div v-if="!documents.length" class="empty-state">
        <p>No documents.</p>
        <span>Upload files to start analyzing.</span>
      </div>
      <ul class="documents-list" v-else>
        <li v-for="doc in documents" :key="doc.id">
          <span class="doc-name">{{ doc.name }}</span>
          <div class="doc-actions">
            <button @click.stop="promptAnalyze(doc)" class="action-btn analyze-btn" title="See the analysis">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
            </button>
            <button @click.stop="promptDelete(doc)" class="action-btn delete-btn" title="Delete document">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
            </button>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import DeleteDocumentModal from '@/components/DeleteDocumentModal.vue';

export default {
  name: 'DocumentsSidebar',
  components: {
    DeleteDocumentModal,
  },
  props: {
    documents: {
      type: Array,
      required: true,
    },
    isCollapsed: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      isDeleteModalOpen: false,
      docToDelete: null,
    };
  },
  methods: {
    triggerFileUpload() {
      this.$refs.fileInput.click();
    },
    handleFileUpload(event) {
      this.$emit('upload-files', event.target.files);
    },
    promptDelete(doc) {
      this.docToDelete = doc;
      this.isDeleteModalOpen = true;
    },
    confirmDelete() {
      this.$emit('delete-document', this.docToDelete.id);
      this.isDeleteModalOpen = false;
      this.docToDelete = null;
    },
    cancelDelete() {
      this.isDeleteModalOpen = false;
      this.docToDelete = null;
    },
    promptAnalyze(doc) {
      this.$emit('analyze-document', doc);
    },
  }
}
</script>

<style scoped>
.documents-sidebar {
  width: 300px;
  border-right: none;
  border-left: 1px solid #1e293b;
  flex-shrink: 0;
  background-color: #162235;
  padding: 20px;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width 0.3s ease, padding 0.3s ease;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

.sidebar-toggle-btn {
  background: none;
  border: none;
  color: #a0aec0;
  cursor: pointer;
  padding: 5px;
  border-radius: 8px;
  transition: background-color 0.3s, color 0.3s;
}

.sidebar-toggle-btn:hover {
  background-color: #1e293b;
  color: #ffffff;
}

/* Collapsed state */
.documents-sidebar.collapsed {
  width: 0;
  padding: 0;
  border: none;
}

.collapsed .sidebar-content {
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.1s ease, visibility 0s linear 0.1s;
}

.documents-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.documents-header h3 {
  font-size: 22px;
  font-weight: 700;
}

.documents-header .sidebar-toggle-btn {
  order: 3;
}

.documents-header .upload-btn {
  order: 2;
  margin-left: auto;
  margin-right: 10px;
}

.upload-btn {
  background-color: #38a169;
  color: #ffffff;
  border: none;
  padding: 8px 15px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-btn:hover {
  background-color: #2f855a;
}

.documents-list {
  list-style: none;
  padding: 0;
  margin: 0;
  overflow-y: auto;
}

.documents-list li {
  background-color: #1e293b;
  padding: 15px;
  border-radius: 10px;
  margin-bottom: 10px;
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.3s;
}

.documents-list li:hover {
  background-color: #2c3a4f;
}

.doc-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: 10px;
  flex-grow: 1;
}

.doc-actions {
  display: flex;
  align-items: center;
  gap: 5px;
  visibility: hidden;
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
}

.documents-list li:hover .doc-actions {
  visibility: visible;
  opacity: 1;
}

.action-btn {
  background: none;
  border: none;
  color: #a0aec0;
  cursor: pointer;
  padding: 5px;
  border-radius: 5px;
  transition: background-color 0.3s, color 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  color: #ffffff;
}

.analyze-btn:hover {
  background-color: #4a90e2;
}

.delete-btn:hover {
  background-color: #e53e3e;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #a0aec0;
}

.empty-state p {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 10px 0;
  color: #ffffff;
}
</style> 