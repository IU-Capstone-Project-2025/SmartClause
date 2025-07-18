import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Spaces API
export const getSpaces = () => apiClient.get('/spaces');
export const createSpace = (data) => apiClient.post('/spaces', data);
export const getSpaceDetails = (spaceId) => apiClient.get(`/spaces/${spaceId}`);
export const updateSpace = (spaceId, data) => apiClient.put(`/spaces/${spaceId}`, data);
export const deleteSpace = (spaceId) => apiClient.delete(`/spaces/${spaceId}`);

// Documents API
export const uploadDocument = (spaceId, file) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post(`/spaces/${spaceId}/documents`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};
export const getDocuments = (spaceId) => apiClient.get(`/spaces/${spaceId}/documents`);
export const getDocumentDetails = (documentId) => apiClient.get(`/documents/${documentId}`);
export const deleteDocument = (documentId) => apiClient.delete(`/documents/${documentId}`);
export const getDocumentAnalysis = (documentId) => apiClient.get(`/documents/${documentId}/analysis`);
export const reanalyzeDocument = (documentId) => apiClient.post(`/documents/${documentId}/reanalyze`);
export const exportAnalysis = (documentId) => apiClient.get(`/documents/${documentId}/analysis/export`, { responseType: 'blob' });

// Handle file upload with duplicate detection
export const uploadDocumentWithDuplicateCheck = async (spaceId, file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await apiClient.post(`/spaces/${spaceId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return { success: true, data: response.data, isDuplicate: false };
  } catch (error) {
    if (error.response && error.response.status === 409) {
      // Duplicate document detected
      return { 
        success: false, 
        isDuplicate: true, 
        duplicateInfo: error.response.data.duplicateInfo,
        message: error.response.data.message 
      };
    }
    throw error; // Re-throw other errors
  }
};

// Messages API
export const getMessages = (spaceId) => apiClient.get(`/spaces/${spaceId}/messages`);
export const sendMessage = (spaceId, message) => apiClient.post(`/spaces/${spaceId}/messages`, message);

// Auth API
export const logout = () => apiClient.post('/auth/logout');
export const getProfile = () => apiClient.get('/auth/profile'); 