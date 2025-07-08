<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <h3>Delete Document</h3>
      <p>Are you sure you want to delete the document "<strong>{{ document.name }}</strong>"? This action cannot be undone.</p>
      <div class="modal-actions">
        <button class="cancel-btn" @click="$emit('close')">Cancel</button>
        <button class="delete-btn" @click="$emit('confirm')">Delete</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DeleteDocumentModal',
  props: {
    document: {
      type: Object,
      required: true,
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: #162235;
  padding: 30px;
  border-radius: 12px;
  width: 100%;
  max-width: 450px;
  border: 1px solid #1e293b;
  color: #ffffff;
}

.modal-content h3 {
  font-size: 24px;
  font-weight: 700;
  margin-top: 0;
  margin-bottom: 20px;
}

.modal-content p {
  margin-bottom: 30px;
  line-height: 1.6;
  color: #a0aec0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
}

.modal-actions button {
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.3s;
}

.cancel-btn {
  background-color: #1e293b;
  color: #ffffff;
}

.cancel-btn:hover {
  background-color: #2d3748;
}

.delete-btn {
  background-color: #e53e3e;
  color: #ffffff;
}

.delete-btn:hover {
  background-color: #c53030;
}
</style> 