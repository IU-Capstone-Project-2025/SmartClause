module.exports = {
  transpileDependencies: [
    'uuid'
  ],
  devServer: {
    public: '0.0.0.0:8080',
    disableHostCheck: true,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        ws: true,
        changeOrigin: true
      }
    }
  }
};