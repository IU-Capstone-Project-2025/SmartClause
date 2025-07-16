<template>
  <div class="auth-screen">
    <div class="auth-container">
      <div class="auth-box">
        <div class="auth-header">
          <h2 class="title">{{ isLogin ? $t('authScreen.welcomeBack') : $t('authScreen.createAccount') }}</h2>
          <p class="subtitle">{{ isLogin ? $t('authScreen.loginToContinue') : $t('authScreen.joinUs') }}</p>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <form @submit.prevent="handleSubmit">
          <div v-if="!isLogin" class="form-grid">
            <div class="form-group">
              <label for="firstname">{{ $t('authScreen.firstName') }}</label>
              <input type="text" id="firstname" v-model="form.first_name" required :placeholder="$t('authScreen.firstNamePlaceholder')">
            </div>
            <div class="form-group">
              <label for="lastname">{{ $t('authScreen.lastName') }}</label>
              <input type="text" id="lastname" v-model="form.last_name" required :placeholder="$t('authScreen.lastNamePlaceholder')">
            </div>
          </div>

          <div class="form-group" v-if="!isLogin">
            <label for="username">{{ $t('authScreen.username') }}</label>
            <input type="text" id="username" v-model="form.username" required :placeholder="$t('authScreen.usernamePlaceholder')">
          </div>

          <div class="form-group">
            <label for="email">{{ isLogin ? $t('authScreen.emailOrUsername') : $t('authScreen.email') }}</label>
            <input type="text" id="email" v-model="form.username_or_email" required :placeholder="isLogin ? $t('authScreen.emailOrUsernamePlaceholder') : $t('authScreen.emailPlaceholder')">
          </div>

          <div class="form-group">
            <label for="password">{{ $t('authScreen.password') }}</label>
            <div class="password-input-wrapper">
              <input :type="showPassword ? 'text' : 'password'" id="password" v-model="form.password" required :minlength="isLogin ? null : 6" :placeholder="$t('authScreen.passwordPlaceholder')">
              <button type="button" class="toggle-password-visibility" @click="togglePasswordVisibility">
                <i :class="showPassword ? 'far fa-eye' : 'far fa-eye-slash'"></i>
              </button>
            </div>
            <p v-if="!isLogin" class="password-hint">{{ $t('authScreen.passwordHint') }}</p>
          </div>

          <div class="form-actions">
            <button type="submit" class="auth-button">
              {{ isLogin ? $t('authScreen.loginButton') : $t('authScreen.createAccountButton') }}
            </button>
          </div>
        </form>

        <div class="switch-auth">
          <p>
            {{ isLogin ? $t('authScreen.noAccount') : $t('authScreen.haveAccount') }}
            <a href="#" @click.prevent="toggleAuthMode">{{ isLogin ? $t('authScreen.signUp') : $t('authScreen.logIn') }}</a>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AuthScreen',
  data() {
    return {
      isLogin: true,
      form: {
        username_or_email: '',
        password: '',
        username: '',
        email: '',
        first_name: '',
        last_name: ''
      },
      error: null,
      showPassword: false
    };
  },
  methods: {
    toggleAuthMode() {
      this.isLogin = !this.isLogin;
      this.resetForm();
    },
    resetForm() {
      this.form.username_or_email = '';
      this.form.password = '';
      this.form.username = '';
      this.form.email = '';
      this.form.first_name = '';
      this.form.last_name = '';
    },
    togglePasswordVisibility() {
      this.showPassword = !this.showPassword;
    },
    async handleSubmit() {
      this.error = null;
      try {
        if (this.isLogin) {
          const response = await axios.post('/api/auth/login', {
            username_or_email: this.form.username_or_email,
            password: this.form.password
          });
          localStorage.setItem('access_token', response.data.access_token);
          const redirectPath = this.$route.query.redirect || '/spaces';
          this.$router.replace(redirectPath);
        } else {
          if (this.form.password.length < 6) {
            this.error = this.$t('authScreen.passwordLengthError');
            return;
          }
          await axios.post('/api/auth/register', {
            username: this.form.username,
            email: this.form.username_or_email,
            password: this.form.password,
            first_name: this.form.first_name,
            last_name: this.form.last_name,
          });
          this.toggleAuthMode();
        }
      } catch (error) {
        if (error.response && error.response.data && error.response.data.detail) {
            this.error = error.response.data.detail;
        } else {
            this.error = this.$t('authScreen.unexpectedError');
        }
        console.error('Authentication error:', error.response ? error.response.data : error.message);
      }
    }
  }
};
</script>

<style scoped>
.auth-screen {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #0c1a2e;
  color: #ffffff;
  font-family: 'Inter', sans-serif;
  position: relative;
  overflow: hidden;
}

.auth-screen::before {
    content: '';
    position: absolute;
    top: -20%;
    left: -20%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(23, 111, 237, 0.2), transparent 70%);
    filter: blur(100px);
    z-index: 0;
}

.auth-container {
  z-index: 1;
}

.error-message {
  background-color: rgba(229, 62, 62, 0.2);
  color: #fca5a5;
  border: 1px solid #ef4444;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  text-align: center;
  font-size: 14px;
}

.auth-box {
  width: 450px;
  background-color: rgba(30, 41, 59, 0.5);
  border: 1px solid #3a4b68;
  border-radius: 20px;
  padding: 40px;
  backdrop-filter: blur(10px);
}

.auth-header {
  text-align: center;
  margin-bottom: 30px;
}

.title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 10px;
}

.subtitle {
  font-size: 16px;
  color: #a0aec0;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  color: #a0aec0;
  margin-bottom: 8px;
}

.form-group input {
  width: 100%;
  background-color: #1e293b;
  border: 1px solid #3a4b68;
  border-radius: 10px;
  padding: 15px;
  color: #ffffff;
  font-size: 16px;
  transition: border-color 0.3s, box-shadow 0.3s;
  box-sizing: border-box;
}

.password-hint {
  font-size: 12px;
  color: #a0aec0;
  margin-top: 5px;
}

.form-group input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3);
}

.password-input-wrapper {
  position: relative;
}

.password-input-wrapper input {
  padding-right: 40px; /* Make space for the eye icon */
}

.toggle-password-visibility {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #a0aec0;
  cursor: pointer;
  font-size: 18px;
  padding: 5px;
  outline: none;
}

.toggle-password-visibility:hover {
  color: #ffffff;
}

.form-actions {
  margin-top: 10px;
}

.auth-button {
  width: 100%;
  background-color: #2563eb;
  color: white;
  border: none;
  padding: 15px 30px;
  margin-top: 20px;
  border-radius: 10px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
  font-weight: 600;
  box-sizing: border-box;
}

.auth-button:hover {
  background-color: #1d4ed8;
}

.switch-auth {
  margin-top: 30px;
  text-align: center;
  font-size: 14px;
  color: #a0aec0;
}

.switch-auth a {
  color: #60a5fa;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s;
}

.switch-auth a:hover {
  color: #ffffff;
}
</style> 