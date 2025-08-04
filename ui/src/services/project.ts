import axios from 'axios';

// 项目信息接口
export interface ProjectInfo {
  id: number;
  name: string;
  path: string;
  description?: string;
  created_at: string;
}

// 请求接口
export interface ProjectCreateRequest {
  name: string;
  path: string;
  description?: string;
}

export interface ProjectListRequest {
  limit?: number;
  offset?: number;
}

export interface ProjectDeleteRequest {
  project_id: number;
}

// 响应接口
export interface ProjectCreateResponse {
  success: boolean;
  message: string;
  project?: ProjectInfo;
}

export interface ProjectListResponse {
  success: boolean;
  message: string;
  projects: ProjectInfo[];
  total: number;
}

export interface ProjectDeleteResponse {
  success: boolean;
  message: string;
}

// 项目服务的基础URL (genie-tool服务运行在1601端口)
const PROJECT_BASE_URL = import.meta.env.DEV
  ? 'http://localhost:1601/v1/project'  // 开发环境
  : 'http://localhost:1601/v1/project'; // 生产环境，可以根据需要修改

// 创建专门用于项目服务的axios实例
const projectRequest = axios.create({
  baseURL: PROJECT_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
projectRequest.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    console.error('项目API请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
projectRequest.interceptors.response.use(
  (response) => {
    return response.data; // 直接返回数据部分
  },
  (error) => {
    console.error('项目API响应错误:', error);

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

// 项目API服务
export const projectApi = {
  // 创建项目
  createProject: (data: ProjectCreateRequest): Promise<ProjectCreateResponse> =>
    projectRequest.post('/create', data),

  // 获取项目列表
  listProjects: (data: ProjectListRequest): Promise<ProjectListResponse> =>
    projectRequest.post('/list', data),

  // 删除项目
  deleteProject: (data: ProjectDeleteRequest): Promise<ProjectDeleteResponse> =>
    projectRequest.post('/delete', data),

  // 健康检查
  healthCheck: () =>
    projectRequest.get('/health'),
};

export default projectApi;
