<template>
  <div id="app">
    <header class="app-header" v-if="showNavBar">
      <div class="logo-container" @click="goHome">
        <svg class="logo-svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>
        <span class="logo-text">SmartClause</span>
      </div>
    </header>
    <main class="main-content" :class="{ 'with-navbar': showNavBar }">
      <transition name="fade" mode="out-in">
        <router-view />
      </transition>
    </main>
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    showNavBar() {
      return this.$route.name !== 'Chat';
    }
  },
  methods: {
    goHome() {
      this.$router.push('/');
    }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');

.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 20px 60px;
  background-color: #0c1a2e;
  color: #ffffff;
  border-bottom: 1px solid #1e293b;
}

.main-content.with-navbar {
  padding-top: 69px; /* Header height + border */
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  width: fit-content;
}

.logo-svg {
  color: #4a90e2;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
}

body {
  margin: 0;
  background-color: #0c1a2e;
}

#app {
  font-family: 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style> 