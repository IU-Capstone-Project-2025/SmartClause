<template>
  <div class="results-screen">
    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>{{ $t('documentAnalysis.loading') }}</p>
    </div>
    <div v-else-if="error" class="error-state">
      <p>{{ $t('documentAnalysis.error') }}</p>
      <p>{{ error }}</p>
    </div>
    <div v-else>
      <div class="results-header">
        <h2>{{ $t('resultsScreen.title') }}</h2>
        <div class="header-controls">
          <button class="export-button" @click="exportAnalysis" :disabled="isExporting" :title="$t('documentAnalysis.exportAnalysisTitle')">
            <div v-if="isExporting" class="button-spinner"></div>
            <DownloadIcon v-else class="export-icon" />
            <span>{{ isExporting ? $t('documentAnalysis.exporting') : $t('documentAnalysis.export') }}</span>
          </button>
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
        <div v-for="(result, index) in results" :key="index" class="result-item">
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
  </div>
</template>

<script>
import { MessageCircle as MessageCircleIcon, Download as DownloadIcon } from 'lucide-vue-next';
import * as api from '@/services/api';

export default {
  name: 'DocumentAnalysis',
  components: {
    MessageCircleIcon,
    DownloadIcon,
  },
  data() {
    return {
      activeIndex: null,
      fileName: '',
      results: [],
      totalIssues: 0,
      isLoading: true,
      error: null,
      isExporting: false,
    };
  },
  async created() {
    await this.fetchAnalysis();
  },
  methods: {
    async fetchAnalysis() {
      this.isLoading = true;
      this.error = null;
      try {
        const documentId = this.$route.params.documentId;
        const response = await api.getDocumentAnalysis(documentId);
        
        // Fetch document details for filename
        const docDetailsResponse = await api.getDocumentDetails(documentId);
        this.fileName = docDetailsResponse.data.document.name || 'Unknown file';

        if (response.data.document_points) {
          this.results = response.data.document_points;
          this.totalIssues = this.results.reduce((total, result) => {
              return total + (result.analysis_points ? result.analysis_points.length : 0);
          }, 0);
        }
      } catch (err) {
        console.error("Error fetching document analysis:", err);
        this.error = err.response?.data?.detail || 'Failed to load analysis results.';
      } finally {
        this.isLoading = false;
      }
    },
    async exportAnalysis() {
      if (this.isExporting) return;
      this.isExporting = true;
      try {
        const documentId = this.$route.params.documentId;
        const response = await api.exportAnalysis(documentId);

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;

        let filename = 'analysis.docx';
        const contentDisposition = response.headers['content-disposition'];
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
            if (filenameMatch && filenameMatch.length > 1) {
                filename = filenameMatch[1];
            }
        } else {
            const originalFilename = this.fileName || 'analysis';
            const baseName = originalFilename.replace(/\.[^/.]+$/, "");
            filename = `${baseName}-analysis.docx`;
        }
        
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Error exporting analysis:', error);
      } finally {
        this.isExporting = false;
      }
    },
    goToChat() {
      const spaceId = this.$route.params.spaceId;
      this.$router.push(`/spaces/${spaceId}`);
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

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  font-size: 20px;
}

.spinner {
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top: 4px solid #ffffff;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.results-header h2 {
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 30px;
}

.button-spinner {
  border: 2px solid rgba(255, 255, 255, 0.5);
  border-top-color: #ffffff;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  animation: spin 0.8s linear infinite;
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

.export-button {
  background-color: #38a169;
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
  margin-right: 10px;
}

.export-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.export-button:hover:not(:disabled) {
  background-color: #2f855a;
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

.result-content p {
  white-space: pre-wrap;
}

.chat-icon {
  width: 20px;
  height: 20px;
}

.export-icon {
  width: 20px;
  height: 20px;
}
</style> 