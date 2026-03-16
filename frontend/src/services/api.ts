/**
 * API 클라이언트 설정
 * FastAPI 서버와 통신 (개발: localhost, 배포: 라즈베리파이 IP)
 */
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// 개발 환경: PC에서 테스트 시 localhost
// 배포 환경: 라즈베리 파이 IP로 변경
const API_BASE_URL = __DEV__
  ? 'http://192.168.0.58:8080'   // Android 에뮬레이터 → 호스트 PC
  : 'http://192.168.0.58:8080'; // 실제 라즈베리 파이
//  : 'http://192.168.0.1:8080'; // 실제 라즈베리 파이 (추후 배포시 주석 풀기)

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// JWT 토큰 인터셉터 - 요청마다 토큰 자동 첨부
apiClient.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 401 응답 시 토큰 삭제
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      await AsyncStorage.removeItem('access_token');
    }
    return Promise.reject(error);
  }
);

// ── 사용자 API ──
export const userAPI = {
  register: (data: { email: string; password: string; user_name: string }) =>
    apiClient.post('/users/register', data),
  login: (data: { email: string; password: string }) =>
    apiClient.post('/users/login', data),
  getProfile: () =>
    apiClient.get('/users/me'),
};

// ── 상품 API ──
export const productAPI = {
  search: (params: {
    keyword?: string;
    category_code?: string;
    page?: number;
    size?: number;
    store_id?: string;
  }) => apiClient.get('/products', { params }),
  getCategories: () =>
    apiClient.get('/products/categories'),
  getDetail: (productId: string) =>
    apiClient.get(`/products/${productId}`),
};

// ── 장바구니 API ──
export const cartAPI = {
  createSession: (storeId?: string) =>
    apiClient.post('/cart/session', { store_id: storeId }),
  getCart: () =>
    apiClient.get('/cart'),
  addItem: (data: { product_id: string; quantity: number; source?: string }) =>
    apiClient.post('/cart/items', data),
  updateItem: (itemId: number, quantity: number) =>
    apiClient.patch(`/cart/items/${itemId}`, { quantity }),
  removeItem: (itemId: number) =>
    apiClient.delete(`/cart/items/${itemId}`),
  clearCart: () =>
    apiClient.delete('/cart/clear'),
};

// ── 경로 API ──
export const routeAPI = {
  optimize: (data: {
    store_id: string;
    product_ids: string[];
    start_node_id?: number;
    end_node_id?: number;
  }) => apiClient.post('/route/optimize', data),
  optimizeFromCart: (data: {
    store_id: string;
    start_node_id?: number;
    end_node_id?: number;
    avoid_congestion?: boolean;
  }) => apiClient.post('/route/optimize-cart', data),
  shortestPath: (data: {
    store_id: string;
    from_node_id: number;
    to_node_id: number;
  }) => apiClient.post('/route/shortest-path', data),
  getNodes: (storeId: string) =>
    apiClient.get('/route/nodes', { params: { store_id: storeId } }),
  getEdges: (storeId: string) =>
    apiClient.get('/route/edges', { params: { store_id: storeId } }),
  // 관리자용 CRUD
  uploadFloorplan: (storeId: string, file: any) => {
    const formData = new FormData();
    formData.append('store_id', storeId);
    formData.append('file', file);
    return apiClient.post('/route/floorplan/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  createNode: (data: {
    store_id: string; x: number; y: number;
    node_type?: string; label?: string; floor?: number;
  }) => {
    const formData = new FormData();
    Object.entries(data).forEach(([k, v]) => { if (v !== undefined) formData.append(k, String(v)); });
    return apiClient.post('/route/nodes', formData);
  },
  updateNode: (nodeId: number, data: {
    x?: number; y?: number; node_type?: string; label?: string;
  }) => {
    const formData = new FormData();
    Object.entries(data).forEach(([k, v]) => { if (v !== undefined) formData.append(k, String(v)); });
    return apiClient.put(`/route/nodes/${nodeId}`, formData);
  },
  deleteNode: (nodeId: number) =>
    apiClient.delete(`/route/nodes/${nodeId}`),
  createEdge: (data: {
    store_id: string; from_node_id: number; to_node_id: number;
    is_bidirectional?: boolean;
  }) => {
    const formData = new FormData();
    Object.entries(data).forEach(([k, v]) => { if (v !== undefined) formData.append(k, String(v)); });
    return apiClient.post('/route/edges', formData);
  },
  deleteEdge: (edgeId: number) =>
    apiClient.delete(`/route/edges/${edgeId}`),
};

// ── AI 채팅 API ──
export const aiAPI = {
  chat: (data: { message: string; store_id?: string }) =>
    apiClient.post('/ai/chat', data),
  getHistory: (limit?: number) =>
    apiClient.get('/ai/history', { params: { limit: limit || 20 } }),
  searchRecipes: (keyword: string) =>
    apiClient.get('/ai/recipes', { params: { keyword } }),
  getAssociations: (productId: string) =>
    apiClient.get(`/ai/associations/${productId}`),
  getTools: () =>
    apiClient.get('/ai/tools'),
};

// ── 결제 API ──
export const paymentAPI = {
  generateQr: (data: { session_id: string; store_id: string }) =>
    apiClient.post('/payment/qr-generate', data),
  confirm: (data: { transaction_id: string; approval_number: string }) =>
    apiClient.post('/payment/confirm', data),
  getTransactions: (limit?: number) =>
    apiClient.get('/payment/transactions', { params: { limit: limit || 20 } }),
  getTransaction: (transactionId: string) =>
    apiClient.get(`/payment/transactions/${transactionId}`),
  getHistory: (limit?: number) =>
    apiClient.get('/payment/history', { params: { limit: limit || 20 } }),
};

// ── 혼잡도 API ──
export const congestionAPI = {
  get: (storeId: string) =>
    apiClient.get(`/congestion/${storeId}`),
  update: (storeId: string, data: { zone_id: number; density_level: number }) =>
    apiClient.put(`/congestion/${storeId}`, data),
  getSummary: (storeId: string) =>
    apiClient.get(`/congestion/${storeId}/summary`),
  simulate: (storeId: string) =>
    apiClient.post(`/congestion/${storeId}/simulate`),
};

// ── IoT API ──
export const iotAPI = {
  getBeacons: (storeId: string) =>
    apiClient.get(`/iot/beacons/${storeId}`),
  reportBeaconSignal: (data: {
    beacon_uuid: string; major: number; minor: number;
    rssi: number; store_id: string;
  }) => apiClient.post('/iot/beacon/signal', data),
  getNfcTags: (storeId: string) =>
    apiClient.get(`/iot/nfc-tags/${storeId}`),
  processNfcTag: (data: { tag_uid: string; store_id: string }) =>
    apiClient.post('/iot/nfc/tag', data),
  updateEsl: (data: {
    mac_address: string; product_name: string;
    regular_price: number; sale_price?: number; store_name?: string;
  }) => apiClient.post('/iot/esl/update', data),
  getDashboard: (storeId: string) =>
    apiClient.get(`/iot/dashboard/${storeId}`),
};

export default apiClient;
