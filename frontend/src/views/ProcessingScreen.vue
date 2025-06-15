<template>
  <div class="processing-screen">
    <div class="results-header">
      <h2>Analysis Results</h2>
      <div class="file-info-bar">
        <span class="file-name">{{ fileName }}</span>
        <div class="status">
          <span class="status-dot"></span>
          <span>Issues found: 0</span>
        </div>
      </div>
    </div>

    <div class="processing-container">
      <div class="processing-content">
        <p class="status-text">Processing data... Please wait.</p>
        <div class="progress-wrapper">
            <p class="progress-label">Analyzing document and preparing recommendations</p>
            <div class="progress-bar-container">
                <div class="progress-bar" :style="{ width: progress + '%' }"></div>
            </div>
            <p class="time-remaining">This will take about {{ formattedTime }}</p>
        </div>
        <button class="cancel-button" @click="cancel">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProcessingScreen',
  data() {
    return {
      progress: 0,
      totalTime: 5, // 4 minutes and 29 seconds
      elapsedTime: 0,
      interval: null,
      fileName: ''
    };
  },
  computed: {
    formattedTime() {
      const remainingTime = this.totalTime - this.elapsedTime;
      const minutes = Math.floor(remainingTime / 60).toString().padStart(2, '0');
      const seconds = (remainingTime % 60).toString().padStart(2, '0');
      return `${minutes}:${seconds}`;
    }
  },
  created() {
    this.fileName = this.$route.query.fileName || 'Unknown file';
  },
  mounted() {
    this.startProgress();
  },
  beforeUnmount() {
    clearInterval(this.interval);
  },
  methods: {
    startProgress() {
      this.interval = setInterval(() => {
        if (this.progress < 100) {
          this.progress += 1;
          this.elapsedTime = Math.floor((this.totalTime * this.progress) / 100);
        } else {
          clearInterval(this.interval);
          this.$router.push({ name: 'Results', query: { fileName: this.fileName } });
        }
      }, (this.totalTime * 1000) / 100);
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

.results-header h2 {
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

.status {
    display: flex;
    align-items: center;
    gap: 10px;
}

.status-dot {
    width: 10px;
    height: 10px;
    background-color: #e53e3e;
    border-radius: 50%;
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
  transition: width 0.1s linear;
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