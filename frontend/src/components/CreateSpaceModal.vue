<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <h3>{{ $t('createSpaceModal.title') }}</h3>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="spaceName">{{ $t('createSpaceModal.nameLabel') }}</label>
          <input type="text" id="spaceName" v-model="spaceName" :placeholder="$t('createSpaceModal.namePlaceholder')" required>
        </div>
        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="$emit('close')">{{ $t('createSpaceModal.cancelButton') }}</button>
          <button type="submit" class="btn-create">{{ $t('createSpaceModal.createButton') }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CreateSpaceModal',
  data() {
    return {
      spaceName: '',
    };
  },
  methods: {
    handleSubmit() {
      if (this.spaceName.trim()) {
        this.$emit('create', this.spaceName.trim());
        this.spaceName = '';
      }
    },
  },
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(12, 26, 46, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  font-family: 'Inter', sans-serif;
}

.modal-content {
  background-color: #162235;
  padding: 30px;
  border-radius: 15px;
  width: 90%;
  max-width: 450px;
  color: #ffffff;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.modal-content h3 {
  font-size: 24px;
  font-weight: 700;
  margin-top: 0;
  margin-bottom: 25px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #a0aec0;
}

.form-group input {
  width: 100%;
  padding: 12px 15px;
  border-radius: 10px;
  border: 1px solid #1e293b;
  background-color: #0c1a2e;
  color: #ffffff;
  font-size: 16px;
  box-sizing: border-box;
}

.form-group input::placeholder {
  color: #a0aec0;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 30px;
}

.form-actions button {
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-size: 16px;
  transition: background-color 0.3s, color 0.3s;
}

.btn-cancel {
  background-color: transparent;
  color: #a0aec0;
}

.btn-cancel:hover {
  background-color: #1e293b;
}

.btn-create {
  background-color: #4a90e2;
  color: #ffffff;
}

.btn-create:hover {
  background-color: #357abd;
}
</style> 