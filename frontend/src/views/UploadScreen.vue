<template>
  <div class="upload-screen">
    <div class="main-content">
      <div class="header">
        <h1 class="title">{{ $t('uploadScreen.title') }}</h1>
        <p class="subtitle">{{ $t('uploadScreen.subtitle') }}</p>
      </div>
      <div class="upload-box-wrapper">
        <div v-if="isAuthorized" class="authorized-suggestion">
          <p>{{ $t('uploadScreen.loggedInSuggestion') }}</p>
          <button class="spaces-button" @click="goToSpaces">{{ $t('uploadScreen.goToSpaces') }}</button>
        </div>
        <div class="upload-box" @dragover.prevent @drop.prevent="handleFileDrop" v-if="!isAuthorized">
          <div class="upload-content">
            <p>{{ $t('uploadScreen.dragAndDrop') }}</p>
            <button class="upload-button" @click="triggerFileInput">
              <Upload :size="20" />
              {{ $t('uploadScreen.selectFile') }}
            </button>
            <p class="formats">{{ $t('uploadScreen.supportedFormats') }}</p>
          </div>
          <input type="file" ref="fileInput" @change="handleFileSelect" style="display: none;" accept=".docx,.pdf">
        </div>
        <p v-if="uploadError" class="error-text">{{ uploadError }}</p>
      </div>
    </div>
    <div class="side-content">
      <div class="info-card">
        <p>{{ $t('uploadScreen.risksInfo') }}</p>
        <div class="icon">
          <FileText :size="24" />
        </div>
      </div>
      <div class="info-card">
        <p>{{ $t('uploadScreen.recommendationsInfo') }}</p>
        <div class="icon">
          <Lightbulb :size="24" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Upload, FileText, Lightbulb } from 'lucide-vue-next';

export default {
  name: 'UploadScreen',
  components: {
    Upload,
    FileText,
    Lightbulb,
  },
  data() {
    return {
      isAuthorized: false,
      uploadError: null,
    };
  },
  created() {
    if (typeof window.localStorage !== 'undefined') {
      this.isAuthorized = !!localStorage.getItem('access_token');
    }
  },
  methods: {
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    handleFileSelect(event) {
      const file = event.target.files[0];
      if (file) {
        this.processFile(file);
      }
    },
    handleFileDrop(event) {
      const file = event.dataTransfer.files[0];
      if (file) {
        this.processFile(file);
      }
    },
    processFile(file) {
      this.uploadError = null;
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        this.uploadError = this.$t('uploadScreen.fileTooLargeError');
        if (this.$refs.fileInput) {
          this.$refs.fileInput.value = '';
        }
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        // eslint-disable-next-line
        const base64String = e.target.result.split(',')[1];
        sessionStorage.setItem('fileToUpload', base64String);
        sessionStorage.setItem('fileName', file.name);
        this.$router.push({ name: 'Processing' });
      };
      reader.readAsDataURL(file);
    },
    goToSpaces() {
      this.$router.push({ name: 'Chat' });
    }
  }
}
</script>

<style scoped>
.upload-screen {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 60px;
  background-color: #0c1a2e;
  color: #ffffff;
  min-height: 100vh;
  font-family: 'Inter', sans-serif;
  position: relative;
  overflow: hidden;
}

.upload-screen::before {
    content: '';
    position: absolute;
    top: -20%;
    left: -20%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(23, 111, 237, 0.2), transparent 70%);
    filter: blur(100px);
    z-index: 0;
}


.main-content {
  flex: 1;
  z-index: 1;
}

.side-content {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  z-index: 1;
}

.header {
  margin-bottom: 60px;
}

.title {
  font-size: 48px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 20px;
}

.subtitle {
  font-size: 20px;
  color: #a0aec0;
}

.error-text {
  color: #ef4444;
  margin-top: 1rem;
  font-size: 14px;
  text-align: center;
}

.upload-box-wrapper {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.upload-box {
  width: 600px;
  height: 300px;
  border: 2px dashed #3a4b68;
  border-radius: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  flex-direction: column;
  transition: background-color 0.3s, border-color 0.3s;
}

.upload-box:hover {
    background-color: rgba(255, 255, 255, 0.05);
    border-color: #4a5b78;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.upload-content p {
    margin-bottom: 20px;
    color: #a0aec0;
}

.upload-button {
  background-color: #2563eb;
  color: white;
  border: none;
  padding: 15px 30px;
  border-radius: 10px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
  display: flex;
  align-items: center;
  gap: 10px;
}

.upload-button:hover {
  background-color: #1d4ed8;
}

.upload-button svg {
    transform: translateY(-1px);
}

.formats {
    font-size: 14px;
    color: #718096;
    margin-top: 20px;
}

.info-card {
  background-color: rgba(30, 41, 59, 0.5);
  border: 1px solid #3a4b68;
  border-radius: 15px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  backdrop-filter: blur(10px);
}

.info-card p {
  flex: 1;
  margin-right: 15px;
}

.info-card .icon {
  background-color: rgba(255, 255, 255, 0.1);
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.info-card .icon svg {
  color: #60a5fa;
  filter: drop-shadow(0 0 8px rgba(96, 165, 250, 1));
}

.authorized-suggestion {
  text-align: center;
  margin-bottom: 40px;
  background-color: rgba(30, 41, 59, 0.5);
  border: 1px solid #3a4b68;
  border-radius: 15px;
  padding: 30px;
  backdrop-filter: blur(10px);
}

.authorized-suggestion p {
  color: #a0aec0;
  margin-bottom: 20px;
}

.spaces-button {
  background-color: #2563eb;
  color: white;
  border: none;
  padding: 15px 30px;
  border-radius: 10px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.spaces-button:hover {
  background-color: #1d4ed8;
}
</style> 