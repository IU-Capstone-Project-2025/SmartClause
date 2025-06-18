<template>
  <div id="app">
    <header class="app-header">
      <div class="logo" @click="goHome">SmartClause</div>
    </header>
    <transition name="fade" mode="out-in">
      <router-view />
    </transition>
  </div>
</template>

<script>
export default {
  name: 'App',
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
  padding: 20px 60px;
  background-color: #0c1a2e;
  color: #ffffff;
  font-size: 20px;
  font-weight: 700;
}

.logo {
  cursor: pointer;
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