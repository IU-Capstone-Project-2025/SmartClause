<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ $t('duplicateDocumentModal.title') }}</h3>
        <button @click="$emit('close')" class="close-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      
      <div class="modal-body">
        <div class="warning-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
            <path d="M12 9v4"/>
            <path d="m12 17 .01 0"/>
          </svg>
        </div>
        
        <div class="duplicate-info">
          <p class="message">{{ duplicateInfo.message }}</p>
          <p class="question">{{ $t('duplicateDocumentModal.question') }}</p>
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="$emit('close')" class="cancel-btn">
          {{ $t('duplicateDocumentModal.cancel') }}
        </button>
        <button @click="$emit('reanalyze')" class="reanalyze-btn">
          {{ $t('duplicateDocumentModal.reanalyze') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DuplicateDocumentModal',
  props: {
    duplicateInfo: {
      type: Object,
      required: true
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: #1e293b;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  color: #ffffff;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #334155;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
}

.close-btn {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: background-color 0.2s, color 0.2s;
}

.close-btn:hover {
  background-color: #374151;
  color: #ffffff;
}

.modal-body {
  padding: 24px;
  text-align: center;
}

.warning-icon {
  margin-bottom: 16px;
  color: #f59e0b;
}

.duplicate-info {
  text-align: center;
}

.message {
  font-size: 16px;
  color: #e5e7eb;
  margin-bottom: 20px;
}

.question {
  font-size: 16px;
  color: #e5e7eb;
  font-weight: 500;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #334155;
}

.cancel-btn, .reanalyze-btn {
  flex: 1;
  padding: 12px 16px;
  border-radius: 8px;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.cancel-btn {
  background-color: #374151;
  border: 1px solid #4b5563;
  color: #e5e7eb;
}

.cancel-btn:hover {
  background-color: #4b5563;
  color: #ffffff;
}

.reanalyze-btn {
  background-color: #dc2626;
  border: 1px solid #dc2626;
  color: #ffffff;
}

.reanalyze-btn:hover {
  background-color: #b91c1c;
  border-color: #b91c1c;
}
</style> 