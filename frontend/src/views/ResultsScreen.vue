<template>
  <div class="results-screen">
    <div class="results-header">
      <h2>Analysis Results</h2>
      <div class="file-info-bar">
        <span class="file-name">{{ fileName }}</span>
        <div class="status">
          <span class="status-dot"></span>
          <span>Issues found: {{ results.length }}</span>
        </div>
      </div>
    </div>

    <div class="results-list">
      <div v-for="(result, index) in results" :key="index" class="result-item">
        <div class="result-item-header" @click="toggleResult(index)">
          <div class="result-title">
            <span>{{ result.title }}</span>
          </div>
          <span class="arrow-icon" :class="{ 'arrow-down': activeIndex === index }">▼</span>
        </div>
        <div v-if="activeIndex === index" class="result-content">
          <p>{{ result.details }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ResultsScreen',
  data() {
    return {
      activeIndex: null,
      fileName: '',
      results: [
        { title: 'Clause 1.1: The address of the apartment (subject of the contract) is not specified.', details: 'The contract does not specify the exact address of the apartment for rent, which could lead to legal disputes.' },
        { title: 'Clause 2.1: An inventory of property is mentioned, but it is missing.', details: 'The contract refers to an appendix with a property inventory, but the appendix itself is not attached to the document.' },
      ]
    };
  },
  created() {
    this.fileName = this.$route.query.fileName || 'Unknown file';
  },
  methods: {
    toggleResult(index) {
      this.activeIndex = this.activeIndex === index ? null : index;
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
</style> 