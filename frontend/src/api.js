import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api', // FastAPI default port
});

export const getDashboardStats = async () => {
  const response = await api.get('/dashboard-stats');
  return response.data;
};

export const getPendingReviews = async () => {
  const response = await api.get('/pending-reviews');
  return response.data;
};

export const resolveReview = async (node_a_id, node_b_id, decision, features = []) => {
  const response = await api.post('/resolve-review', {
    node_a_id,
    node_b_id,
    decision,
    features,
  });
  return response.data;
};

export const searchBusinesses = async (query) => {
  const response = await api.get(`/search`, { params: { query } });
  return response.data;
};

export const getUbidDetails = async (ubid) => {
  const response = await api.get(`/ubid/${ubid}`);
  return response.data;
};
