<template>
  <div class="upload-screen">
    <div class="main-content">
      <div class="header">
        <h1 class="title">Secure deals start here</h1>
        <p class="subtitle">Upload a contract, and our AI assistant will identify risks and suggest improvements.</p>
      </div>
      <div class="upload-box-wrapper">
        <div class="upload-box" @dragover.prevent @drop.prevent="handleFileDrop">
          <div class="upload-content">
            <p>Drag and drop your document here or select a file</p>
            <button class="upload-button" @click="triggerFileInput">
              <Upload :size="20" />
              Select File
            </button>
            <p class="formats">Supported formats: .docx, .png, .jpg, .jpeg</p>
          </div>
          <input type="file" ref="fileInput" @change="handleFileSelect" style="display: none;" accept=".docx,.png,.jpg,.jpeg">
        </div>
      </div>
    </div>
    <div class="side-content">
      <div class="info-card">
        <p>We find hidden risks and check for legal compliance.</p>
        <div class="icon">
          <FileText :size="24" />
        </div>
      </div>
      <div class="info-card">
        <p>We provide clear recommendations for improving each clause of the contract.</p>
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
      const reader = new FileReader();
      reader.onload = (e) => {
        // eslint-disable-next-line
        const base64String = e.target.result.split(',')[1];
        sessionStorage.setItem('fileToUpload', base64String);
        sessionStorage.setItem('fileName', file.name);
        this.$router.push({ name: 'Processing' });
      };
      reader.readAsDataURL(file);
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

.upload-box-wrapper {
  display: flex;
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
</style> 