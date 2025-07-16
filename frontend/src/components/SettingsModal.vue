<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <button class="close-x-button" @click="$emit('close')">
        <x-icon size="24" />
      </button>
      <h3>{{ $t('settingsModal.title') }}</h3>
      <div v-if="user" class="user-profile">
        <div class="user-avatar">
          <span>{{ user.initials }}</span>
        </div>
        <div class="user-info">
          <p class="user-name">{{ user.full_name }}</p>
          <p class="user-email">{{ user.email }}</p>
        </div>
      </div>
      <div class="language-selector">
        <label for="language-select">{{ $t('settingsModal.languageLabel') }}</label>
        <select id="language-select" v-model="selectedLanguage" @change="switchLanguage">
          <option value="en">English</option>
          <option value="ru">Русский</option>
        </select>
      </div>
      <div class="form-actions">
        <button type="button" class="btn-logout" @click="handleLogout">
          <log-out-icon size="18" />
          <span>{{ $t('settingsModal.logoutButton') }}</span>
        </button>
        <!-- <button type="button" class="btn-cancel" @click="$emit('close')">{{ $t('settingsModal.closeButton') }}</button> -->
      </div>
    </div>
  </div>
</template>

<script>
import { LogOut as LogOutIcon, X as XIcon } from 'lucide-vue-next';

export default {
  name: 'SettingsModal',
  components: {
    LogOutIcon,
    XIcon,
  },
  props: {
    user: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      selectedLanguage: this.$i18n.locale,
    };
  },
  methods: {
    handleLogout() {
      this.$emit('logout');
    },
    switchLanguage() {
      this.$i18n.locale = this.selectedLanguage;
      localStorage.setItem('language', this.selectedLanguage);
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
  position: relative;
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

.close-x-button {
  position: absolute;
  top: 15px;
  right: 15px;
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
  color: #a0aec0;
  transition: color 0.3s ease;
}

.close-x-button:hover {
  color: #ffffff;
}

.language-selector {
  margin-bottom: 20px;
}

.language-selector label {
  display: block;
  margin-bottom: 8px;
  color: #a0aec0;
  font-size: 14px;
}

.language-selector select {
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #3a4b68;
  background-color: #1e293b;
  color: #ffffff;
  font-size: 16px;
}

.user-profile {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
}

.user-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: #4a90e2;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  margin-right: 20px;
}

.user-info .user-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.user-info .user-email {
  font-size: 14px;
  color: #a0aec0;
  margin: 5px 0 0 0;
}

.form-actions {
  display: flex;
  justify-content: space-between;
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

.btn-logout {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: #e53e3e;
  color: #ffffff;
}

.btn-logout:hover {
  background-color: #c53030;
}
</style> 