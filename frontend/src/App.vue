<template>
  <div id="app">
    <h1>{{ backendMessage }}</h1>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'App',
  data() {
    return {
      backendMessage: 'Hello World',
    };
  },
  mounted() {
    axios.get('/api/message')
      .then(response => {
        this.backendMessage = response.data.message;
      })
      .catch(error => {
        console.error('Error fetching message from backend:', error);
      });
  },
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style> 