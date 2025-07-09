<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <h3>Edit Space</h3>
      <form @submit.prevent="submitEdit">
        <label for="space-name">Space Name</label>
        <input id="space-name" v-model="editableSpaceName" type="text" required>
        <div class="modal-actions">
          <button type="button" class="cancel-btn" @click="$emit('close')">Cancel</button>
          <button type="submit" class="save-btn">Save</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'EditSpaceModal',
  props: {
    space: {
      type: Object,
      required: true,
    }
  },
  data() {
    return {
      editableSpaceName: ''
    };
  },
  watch: {
    space: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.editableSpaceName = newVal.name;
        }
      }
    }
  },
  methods: {
    submitEdit() {
      if (this.editableSpaceName.trim()) {
        this.$emit('update', { ...this.space, name: this.editableSpaceName });
      }
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

form {
  display: flex;
  flex-direction: column;
}

label {
  margin-bottom: 10px;
  font-weight: 600;
}

input {
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #3c4a5f;
  background-color: #0c1a2e;
  color: #ffffff;
  margin-bottom: 20px;
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

.save-btn {
  background-color: #4a90e2;
  color: #ffffff;
}

.save-btn:hover {
  background-color: #3B7BC4;
}
</style> 