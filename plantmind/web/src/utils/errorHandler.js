/**
 * API Error Handler - Provides user-friendly error messages
 */

export const getErrorMessage = (error, apiBase) => {
  if (!error) return 'An unknown error occurred';
  
  // Network errors
  if (error.message === 'Network Error') {
    return `Cannot connect to the backend API. Make sure your backend is running and accessible at: ${apiBase}`;
  }
  
  // Axios errors
  if (error.response) {
    const status = error.response.status;
    const data = error.response.data;
    
    switch (status) {
      case 400:
        return data?.detail || 'Invalid request to the backend';
      case 401:
        return 'Authentication required. Please contact administrator';
      case 403:
        return 'Access forbidden. You do not have permission';
      case 404:
        return `Backend endpoint not found. Verify API_BASE is correct: ${apiBase}`;
      case 500:
        return 'Backend server error. Please try again later';
      case 503:
        return 'Backend service unavailable. Please try again later';
      default:
        return `Backend error (${status}): ${data?.detail || error.message}`;
    }
  }
  
  // Timeout errors
  if (error.code === 'ECONNABORTED') {
    return 'Request timeout. Backend is taking too long to respond';
  }
  
  return error.message || 'Failed to connect to the backend';
};

export default {
  getErrorMessage
};
