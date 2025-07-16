<template>
  <div class="spaces-sidebar" :class="{ 'collapsed': isCollapsed }">
    <CreateSpaceModal v-if="isModalOpen" @close="isModalOpen = false" @create="handleCreateSpace" />
    <DeleteSpaceModal 
        v-if="isDeleteModalOpen" 
        :space="spaceToDelete" 
        @close="cancelDelete" 
        @confirm="confirmDeleteSpace" />
    <EditSpaceModal
        v-if="isEditModalOpen"
        :space="spaceToEdit"
        @close="cancelEdit"
        @update="handleUpdateSpace" />
    <SettingsModal
        v-if="isSettingsModalOpen"
        :user="user"
        @close="isSettingsModalOpen = false"
        @logout="handleLogout" />

    <div class="sidebar-content">
      <div class="app-branding-container">
        <div class="app-branding" @click="goHome" title="SmartClause">
          <svg class="logo" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>
          <h1 class="app-title">SmartClause</h1>
        </div>
        <button @click.stop="$emit('toggle-collapse')" class="sidebar-toggle-btn" :title="$t('spacesSidebar.title')">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
        </button>
      </div>
      <div class="spaces-header">
        <h3>{{ $t('spacesSidebar.title') }}</h3>
        <button class="create-space-btn" @click="isModalOpen = true" :title="$t('spacesSidebar.newSpace')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
      </div>
      <div v-if="!spaces.length" class="empty-state">
        <p>{{ $t('spacesSidebar.noSpaces') }}</p>
        <span>{{ $t('spacesSidebar.createSpace') }}</span>
      </div>
      <ul class="spaces-list" v-else>
        <li v-for="space in spaces" :key="space.id" @click="$emit('select-space', space.id)" :class="{ active: space.id === selectedSpaceId }">
          <span class="space-name" :title="space.name">{{ space.name }}</span>
          <div class="space-actions">
            <button @click.stop="promptEditSpace(space)" class="action-btn edit-btn" title="Edit space">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
            </button>
            <button @click.stop="promptDeleteSpace(space)" class="action-btn delete-btn" title="Delete space">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
          </button>
          </div>
        </li>
      </ul>
    </div>
    <div class="sidebar-footer" v-if="!isCollapsed">
        <div v-if="user" class="user-profile" @click="isSettingsModalOpen = true">
            <div class="user-avatar">
                <span>{{ userInitials }}</span>
            </div>
            <div class="user-info">
                <span class="user-name" :title="user.full_name">{{ user.full_name }}</span>
            </div>
             <button class="action-btn settings-btn" :title="$t('spacesSidebar.settings')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
            </button>
        </div>
    </div>
  </div>
</template>

<script>
import CreateSpaceModal from '@/components/CreateSpaceModal.vue';
import DeleteSpaceModal from '@/components/DeleteSpaceModal.vue';
import EditSpaceModal from '@/components/EditSpaceModal.vue';
import SettingsModal from '@/components/SettingsModal.vue';
import * as api from '@/services/api';

export default {
  name: 'SpacesSidebar',
  components: {
    CreateSpaceModal,
    DeleteSpaceModal,
    EditSpaceModal,
    SettingsModal,
  },
  props: {
    spaces: {
      type: Array,
      required: true,
    },
    selectedSpaceId: {
      type: Number,
      default: null,
    },
    isCollapsed: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      isModalOpen: false,
      isDeleteModalOpen: false,
      spaceToDelete: null,
      isEditModalOpen: false,
      spaceToEdit: null,
      isSettingsModalOpen: false,
      user: null,
    };
  },
  computed: {
    userInitials() {
      if (this.user && this.user.full_name) {
        return this.user.full_name.split(' ').map(n => n[0]).join('').toUpperCase();
      }
      return '';
    }
  },
  methods: {
    goHome() {
      this.$router.push('/');
    },
    promptDeleteSpace(space) {
      this.spaceToDelete = space;
      this.isDeleteModalOpen = true;
    },
    confirmDeleteSpace() {
      this.$emit('delete-space', this.spaceToDelete.id);
      this.isDeleteModalOpen = false;
      this.spaceToDelete = null;
    },
    cancelDelete() {
      this.isDeleteModalOpen = false;
      this.spaceToDelete = null;
    },
    handleCreateSpace(spaceName) {
      this.$emit('create-space', spaceName);
      this.isModalOpen = false;
    },
    promptEditSpace(space) {
      this.spaceToEdit = space;
      this.isEditModalOpen = true;
    },
    cancelEdit() {
      this.isEditModalOpen = false;
      this.spaceToEdit = null;
    },
    handleUpdateSpace(updatedSpace) {
      this.$emit('update-space', updatedSpace);
      this.cancelEdit();
    },
    async fetchUserProfile() {
      try {
        const response = await api.getProfile();
        this.user = response.data;
      } catch (error) {
        console.error('Error fetching user profile:', error);
        // Could redirect to login if profile fetch fails due to auth error
        if (error.response && error.response.status === 401) {
          this.$router.push('/login');
        }
      }
    },
    async handleLogout() {
      try {
        await api.logout();
      } catch (error) {
        console.error('Logout failed', error);
      } finally {
        localStorage.removeItem('access_token');
        this.$router.push('/login');
      }
    }
  },
  created() {
    this.fetchUserProfile();
  }
}
</script>

<style scoped>
.spaces-sidebar {
  flex-shrink: 0;
  width: 260px;
  background-color: #162235;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border-right: 1px solid #1e293b;
  position: relative;
  transition: width 0.3s ease, padding 0.3s ease;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  flex-grow: 1;
}

.sidebar-toggle-btn {
  background: none;
  border: none;
  color: #a0aec0;
  cursor: pointer;
  padding: 5px;
  border-radius: 8px;
  transition: background-color 0.3s, color 0.3s;
}

.sidebar-toggle-btn:hover {
  background-color: #1e293b;
  color: #ffffff;
}

/* Collapsed state */
.spaces-sidebar.collapsed {
  width: 0;
  padding: 0;
  border: none;
}

.collapsed .sidebar-content {
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.1s ease, visibility 0s linear 0.1s;
}

.app-branding-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 10px 30px 10px;
  border-bottom: 1px solid #1e293b;
  margin-bottom: 20px;
}

.app-branding {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.app-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
}

.logo {
  color: #4a90e2;
}

.spaces-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.spaces-header h3 {
  font-size: 22px;
  font-weight: 700;
}

.create-space-btn {
  background-color: transparent;
  color: #a0aec0;
  border: 1px dashed #a0aec0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.create-space-btn:hover {
  background-color: #4a90e2;
  color: #ffffff;
  border-color: #4a90e2;
}

.spaces-list {
  list-style: none;
  padding: 0;
  margin: 0;
  overflow-y: auto;
}

.spaces-list li {
  padding: 15px;
  border-radius: 10px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: background-color 0.3s, color 0.3s;
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.spaces-list li:hover {
  background-color: #1e293b;
}

.spaces-list li.active {
  background-color: #4a90e2;
  color: #ffffff;
  font-weight: 600;
}

.space-name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-right: 10px;
}

.space-actions {
  display: flex;
  align-items: center;
  gap: 5px;
  visibility: hidden;
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
}

.spaces-list li:hover .space-actions {
  visibility: visible;
  opacity: 1;
}

.action-btn {
  background: none;
  border: none;
  color: #a0aec0;
  cursor: pointer;
  padding: 5px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease-in-out;
}

.action-btn:hover {
  color: #ffffff;
}

.edit-btn:hover {
  background-color: #dd6b20;
}

.delete-btn {
  /* No special hover because it's handled in a modal */
}

.delete-btn:hover {
    background-color: #e53e3e;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #a0aec0;
}

.empty-state p {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 10px 0;
  color: #ffffff;
}

.sidebar-footer {
    padding: 20px;
    border-top: 1px solid #1e293b;
}

.user-profile {
    display: flex;
    align-items: center;
    cursor: pointer;
    padding: 10px;
    border-radius: 10px;
    transition: background-color 0.3s;
}

.user-profile:hover {
    background-color: #1e293b;
}

.user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: #4a90e2;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 700;
    margin-right: 12px;
    flex-shrink: 0;
}

.user-info {
    flex-grow: 1;
    overflow: hidden;
    margin-right: 10px;
}

.user-name {
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.settings-btn:hover {
    background-color: #6366f1;
}
</style> 