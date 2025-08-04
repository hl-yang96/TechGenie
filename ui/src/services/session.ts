import axios from 'axios';

// 聊天会话接口
export interface ChatSessionData {
  chatTitle?: string;
  sessionId?: string;
  chatList?: any[];
  [key: string]: any;
}

// 请求接口
export interface ChatSessionCreateRequest {
  reqId: string;
  data?: ChatSessionData;
}

export interface ChatSessionUpdateRequest {
  reqId: string;
  data: ChatSessionData;
}

export interface ChatSessionGetRequest {
  reqId: string;
}

export interface ChatSessionListRequest {
  limit?: number;
  offset?: number;
}

export interface ChatSessionDeleteRequest {
  reqId: string;
}

// 响应接口
export interface ChatSessionResponse {
  success: boolean;
  message: string;
  data?: ChatSessionData;
}

export interface ChatSessionCreateResponse {
  success: boolean;
  message: string;
  data?: { req_id: string };
}

export interface ChatSessionInfo {
  reqId: string;
  chatTitle?: string;
  createdAt: string;
  updatedAt?: string;
}

export interface ChatSessionListResponse {
  success: boolean;
  message: string;
  sessions: ChatSessionInfo[];
  total: number;
}

export interface ChatSessionDeleteResponse {
  success: boolean;
  message: string;
}

// 会话服务的基础URL (genie-tool服务运行在1601端口)
const SESSION_BASE_URL = import.meta.env.DEV
  ? 'http://localhost:1601/v1/session'  // 开发环境
  : 'http://localhost:1601/v1/session'; // 生产环境，可以根据需要修改

// 创建专门用于会话服务的axios实例
const sessionRequest = axios.create({
  baseURL: SESSION_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
sessionRequest.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    console.error('会话API请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
sessionRequest.interceptors.response.use(
  (response) => {
    return response.data; // 直接返回数据部分
  },
  (error) => {
    console.error('会话API响应错误:', error);

    if (error.response) {
      const { status, data } = error.response;
      console.error(`HTTP ${status}:`, data);
    } else if (error.request) {
      console.error('网络错误:', error.request);
    } else {
      console.error('请求配置错误:', error.message);
    }

    return Promise.reject(error);
  }
);

// 会话API服务
export const sessionApi = {
  // 创建会话
  createSession: (data: ChatSessionCreateRequest): Promise<ChatSessionCreateResponse> =>
    sessionRequest.post('/create', data),

  // 更新会话
  updateSession: (data: ChatSessionUpdateRequest): Promise<ChatSessionResponse> =>
    sessionRequest.post('/update', data),

  // 获取会话
  getSession: (data: ChatSessionGetRequest): Promise<ChatSessionResponse> =>
    sessionRequest.post('/get', data),

  // 获取会话列表
  listSessions: (data: ChatSessionListRequest): Promise<ChatSessionListResponse> =>
    sessionRequest.post('/list', data),

  // 删除会话
  deleteSession: (data: ChatSessionDeleteRequest): Promise<ChatSessionDeleteResponse> =>
    sessionRequest.post('/delete', data),
};

export default sessionApi;
