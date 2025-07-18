<template>
  <div class="results-screen">
    <div class="results-header">
      <h2>{{ $t('resultsScreen.title') }}</h2>
      <div class="header-controls">
        <button class="chat-button" @click="goToChat">
          <MessageCircleIcon class="chat-icon" />
          <span>{{ $t('resultsScreen.askQuestion') }}</span>
        </button>
      </div>
      <div class="file-info-bar">
        <span class="file-name">{{ fileName }}</span>
        <div class="status">
          <span class="status-dot"></span>
          <span>{{ $t('resultsScreen.issuesFound', { count: totalIssues }) }}</span>
        </div>
      </div>
    </div>

    <div class="results-list">
      <div v-for="(result, index) in filteredResults" :key="index" class="result-item">
        <div class="result-item-header" @click="toggleResult(index)">
          <div class="result-title">
            <span>{{ result.point_number }}: {{ activeIndex === index ? result.point_content : truncate(result.point_content, 100) }}</span>
          </div>
          <span class="arrow-icon" :class="{ 'arrow-down': activeIndex === index }">▼</span>
        </div>
        <div v-if="activeIndex === index" class="result-content">
          <div v-for="(analysis, analysisIndex) in result.analysis_points" :key="analysisIndex" class="analysis-item">
            <h4>{{ $t('resultsScreen.issue') }} {{ analysisIndex + 1 }}</h4>
            <p><strong>{{ $t('resultsScreen.cause') }}:</strong> {{ analysis.cause }}</p>
            <p><strong>{{ $t('resultsScreen.risk') }}:</strong> <span :class="getRiskClass(analysis.risk)">{{ analysis.risk }}</span></p>
            <p><strong>{{ $t('resultsScreen.recommendation') }}:</strong> {{ analysis.recommendation }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { MessageCircle as MessageCircleIcon } from 'lucide-vue-next';

export default {
  name: 'ResultsScreen',
  components: {
    MessageCircleIcon
  },
  data() {
    return {
      activeIndex: null,
      fileName: '',
      results: [],
    };
  },
  computed: {
    filteredResults() {
      return this.results.filter(result => result.analysis_points && result.analysis_points.length > 0);
    },
    totalIssues() {
      return this.filteredResults.reduce((total, result) => {
        return total + (result.analysis_points ? result.analysis_points.length : 0);
      }, 0);
    }
  },
  created() {
    this.fileName = this.$route.query.fileName || 'Unknown file';
    const resultsData = sessionStorage.getItem('analysisResults');
    if (resultsData) {
      const apiResponse = JSON.parse(resultsData);
      if (apiResponse.document_points) {
        this.results = apiResponse.document_points;
      }
    } else {
      this.$router.push('/');
    }
  },
  methods: {
    goToChat() {
      this.$router.push('/spaces/1');
    },
    toggleResult(index) {
      this.activeIndex = this.activeIndex === index ? null : index;
    },
    truncate(text, length) {
        if (text && text.length > length) {
            return text.substring(0, length) + '...';
        }
        return text;
    },
    getRiskClass(risk) {
        if (!risk) return '';
        const riskLowerCase = risk.toLowerCase();
        if (riskLowerCase.includes('высокий') || riskLowerCase.includes('high')) {
            return 'risk-high';
        }
        if (riskLowerCase.includes('средний') || riskLowerCase.includes('medium')) {
            return 'risk-medium';
        }
        if (riskLowerCase.includes('низкий') || riskLowerCase.includes('low')) {
            return 'risk-low';
        }
        return '';
    }
  }
}
</script>

<style scoped>
.results-screen {
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

.header-controls {
  margin-bottom: 20px;
  text-align: right;
}

.chat-button {
  background-color: #4a90e2;
  color: #ffffff;
  border: none;
  padding: 12px 25px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  font-size: 16px;
  transition: background-color 0.3s;
  font-family: 'Inter', sans-serif;
  display: inline-flex;
  gap: 10px;
}

.chat-button:hover {
  background-color: #357abd;
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

.results-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.result-item {
    background-color: #162235;
    border-radius: 15px;
    overflow: hidden;
    transition: background-color 0.3s;
}

.result-item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 25px;
    cursor: pointer;
    line-height: 1.5;
}

.result-title {
    display: flex;
    align-items: center;
}

.arrow-icon {
    font-size: 14px;
    transition: transform 0.3s;
}

.arrow-down {
    transform: rotate(180deg);
}

.result-content {
    padding: 0 25px 20px 25px;
    color: #a0aec0;
    border-top: 1px solid #1e293b;
    margin-top: 15px;
    padding-top: 20px;
}

.analysis-item {
    background-color: #1e293b;
    border-radius: 10px;
    padding: 15px 20px;
    margin-bottom: 15px;
}

.analysis-item:last-child {
    margin-bottom: 0;
}

.analysis-item h4 {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 10px;
    color: #ffffff;
}

.analysis-item p {
    margin-bottom: 8px;
    line-height: 1.6;
}

.analysis-item p strong {
    color: #cbd5e0;
}

.risk-high {
    color: #e53e3e;
    font-weight: bold;
}

.risk-medium {
    color: #dd6b20;
    font-weight: bold;
}

.risk-low {
    color: #38a169;
    font-weight: bold;
}

.risk-high::after {
    content: " ({{ $t('resultsScreen.riskHigh') }})";
}

.risk-medium::after {
    content: " ({{ $t('resultsScreen.riskMedium') }})";
}

.risk-low::after {
    content: " ({{ $t('resultsScreen.riskLow') }})";
}

.result-content p {
  white-space: pre-wrap;
}

.chat-icon {
  width: 20px;
  height: 20px;
}
</style> 