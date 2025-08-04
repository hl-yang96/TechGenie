import axios from 'axios';

// 文件信息接口
export interface FileInfo {
  ossUrl: string;
  downloadUrl: string;
  domainUrl: string;
  requestId: string;
  fileName: string;
}

// 文件列表请求接口
export interface FileListRequest {
  requestId: string;
  filters?: Array<{
    requestId: string;
    fileName: string;
  }>;
  page?: number;
  pageSize?: number;
}

// 文件列表响应接口
export interface FileListResponse {
  results: FileInfo[];
  totalSize: number;
}

// 文件服务的基础URL (genie-tool服务运行在1601端口)
const FILE_BASE_URL = import.meta.env.DEV
  ? 'http://localhost:1601/v1/file_tool'  // 开发环境
  : 'http://localhost:1601/v1/file_tool'; // 生产环境，可以根据需要修改

// 创建专门用于文件服务的axios实例
const fileRequest = axios.create({
  baseURL: FILE_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
fileRequest.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    console.error('文件API请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
fileRequest.interceptors.response.use(
  (response) => {
    return response.data; // 直接返回数据部分
  },
  (error) => {
    console.error('文件API响应错误:', error);

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

// 文件API服务
export const fileApi = {
  // 获取文件列表
  getFileList: (data: FileListRequest): Promise<FileListResponse> =>
    fileRequest.post('/get_file_list', data),
};

export default fileApi;
