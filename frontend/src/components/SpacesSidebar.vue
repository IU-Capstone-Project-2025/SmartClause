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

    <div class="sidebar-content">
      <div class="app-branding-container">
        <div class="app-branding" @click="goHome" title="Go to homepage">
          <svg class="logo" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>
          <h1 class="app-title">SmartClause</h1>
        </div>
        <button @click.stop="$emit('toggle-collapse')" class="sidebar-toggle-btn" title="Collapse sidebar">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
        </button>
      </div>
      <div class="spaces-header">
        <h3>Spaces</h3>
        <button class="create-space-btn" @click="isModalOpen = true" title="Create new space">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
      </div>
      <div v-if="!spaces.length" class="empty-state">
        <p>No spaces yet.</p>
        <span>Create one to start collaborating.</span>
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
  </div>
</template>

<script>
import CreateSpaceModal from '@/components/CreateSpaceModal.vue';
import DeleteSpaceModal from '@/components/DeleteSpaceModal.vue';
import EditSpaceModal from '@/components/EditSpaceModal.vue';

export default {
  name: 'SpacesSidebar',
  components: {
    CreateSpaceModal,
    DeleteSpaceModal,
    EditSpaceModal,
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
    };
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
  border-right: 1px solid #1e293b;
  position: relative;
  transition: width 0.3s ease, padding 0.3s ease;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
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
</style> 