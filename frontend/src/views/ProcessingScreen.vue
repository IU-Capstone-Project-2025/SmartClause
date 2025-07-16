<template>
  <div class="processing-screen">
    <div class="processing-header">
      <h2>{{ $t('processingScreen.title') }}</h2>
      <div class="file-info-bar">
        <span class="file-name">{{ fileName }}</span>
      </div>
    </div>

    <div class="processing-container">
      <div class="processing-content">
        <p class="status-text">{{ statusText }}</p>
        <div class="progress-wrapper">
          <p class="progress-label">{{ $t('processingScreen.progressLabel') }}</p>
          <div class="progress-bar-container">
            <div class="progress-bar"></div>
          </div>
          <p class="time-remaining">{{ $t('processingScreen.timeRemaining') }}</p>
        </div>
        <!-- <button class="cancel-button" @click="cancel">{{ $t('processingScreen.cancelButton') }}</button> -->
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

export default {
  name: 'ProcessingScreen',
  data() {
    return {
      fileName: '',
      statusText: ''
    };
  },
  created() {
    this.fileName = sessionStorage.getItem('fileName') || 'Unknown file';
    this.statusText = this.$t('processingScreen.statusProcessing');
  },
  mounted() {
    this.uploadAndProcessFile();
  },
  methods: {
    uploadAndProcessFile() {
      const fileData = sessionStorage.getItem('fileToUpload');
      if (!fileData) {
        this.$router.push('/');
        return;
      }

      this.statusText = this.$t('processingScreen.statusUploading');

      // Convert base64 string back to file for multipart upload
      const byteCharacters = atob(fileData);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const file = new Blob([byteArray], { type: 'application/octet-stream' });

      // Create FormData for multipart upload
      const formData = new FormData();
      formData.append('id', uuidv4());
      formData.append('bytes', file, this.fileName);

      axios.post('/api/v1/get_analysis', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
        .then(response => {
          this.statusText = this.$t('processingScreen.statusComplete');
          sessionStorage.setItem('analysisResults', JSON.stringify(response.data));
          this.$router.push({ name: 'Results', query: { fileName: this.fileName } });
        })
        .catch(error => {
          console.error('Processing failed:', error);
          this.statusText = this.$t('processingScreen.statusError');
          // Optionally, redirect back to upload screen after a delay
          setTimeout(() => this.$router.push('/'), 2000);
        });
    },
    cancel() {
      this.$router.push('/');
    }
  }
}
</script>

<style scoped>
.processing-screen {
  padding: 60px;
  background-color: #0c1a2e;
  color: #ffffff;
  min-height: 100vh;
  font-family: 'Inter', sans-serif;
}

.processing-header h2 {
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 30px;
}

.file-info-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: #1e293b;
    padding: 15px 25px;
    border-radius: 15px;
    margin-bottom: 40px;
}

.file-name {
    font-weight: 500;
}

.processing-container {
  background-color: #162235;
  border-radius: 20px;
  padding: 60px;
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.processing-content {
    width: 600px;
}

.status-text {
  color: #a0aec0;
  margin-bottom: 40px;
  font-style: italic;
}

.progress-wrapper {
  background-color: #0c1a2e;
  border-radius: 15px;
  padding: 30px;
}

.progress-label {
    margin-bottom: 15px;
    font-weight: 500;
}

.progress-bar-container {
  background-color: #1e293b;
  border-radius: 10px;
  height: 20px;
  overflow: hidden;
  margin-bottom: 15px;
}

.progress-bar {
  background-color: #2563eb;
  height: 100%;
  border-radius: 10px;
  width: 100%;
  background-image: linear-gradient(
    -45deg,
    rgba(255, 255, 255, 0.2) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255, 255, 255, 0.2) 50%,
    rgba(255, 255, 255, 0.2) 75%,
    transparent 75%,
    transparent
  );
  background-size: 40px 40px;
  animation: progress-animation 2s linear infinite;
}

@keyframes progress-animation {
  0% {
    background-position: 40px 0;
  }
  100% {
    background-position: 0 0;
  }
}

.time-remaining {
  color: #a0aec0;
  font-size: 14px;
}

.cancel-button {
  background-color: transparent;
  color: #a0aec0;
  border: 1px solid #3a4b68;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s, color 0.3s;
  margin-top: 40px;
}

.cancel-button:hover {
  background-color: #1e293b;
  color: #ffffff;
}
</style> 