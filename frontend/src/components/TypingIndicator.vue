<template>
  <div class="typing-indicator">
    <span class="dot"></span>
    <span class="dot"></span>
    <span class="dot"></span>
  </div>
</template>

<script>
export default {
  name: 'TypingIndicator'
}
</script>

<style scoped>
.typing-indicator {
  display: flex;
  align-items: center;
  padding: 10px 0;
}

.dot {
  width: 8px;
  height: 8px;
  margin: 0 3px;
  background-color: #a0aec0;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1.0);
  }
}
</style> 