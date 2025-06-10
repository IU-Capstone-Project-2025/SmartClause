module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        ws: true,
        changeOrigin: true
      }
    }
  }
} 