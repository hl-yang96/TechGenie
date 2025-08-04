import axios from 'axios';

// RAG服务的基础URL (genie-tool服务运行在1601端口)
const RAG_BASE_URL = import.meta.env.DEV
  ? 'http://localhost:1601/v1/rag'  // 开发环境
  : 'http://localhost:1601/v1/rag'; // 生产环境，可以根据需要修改

// 创建专门用于RAG服务的axios实例
const ragRequest = axios.create({
  baseURL: RAG_BASE_URL,
  timeout: 30000, // RAG操作可能需要更长时间
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
ragRequest.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    console.error('RAG请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
ragRequest.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('RAG响应错误:', error);
    const message = error.response?.data?.detail || error.message || 'RAG服务请求失败';
    return Promise.reject(new Error(message));
  }
);

// RAG文档接口类型定义
export interface RAGDocument {
  document_id: string;
  filename: string;
  file_path: string;
  collection_type: string;
  file_size: number;
  file_description?: string;
  file_abstract?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RAGIngestRequest {
  requestId: string;
  documentPath?: string;
  documentContent?: string;
  collectionType?: string;
}

export interface RAGListRequest {
  requestId: string;
  collectionType?: string;
  filenamePattern?: string;
  limit?: number;
  offset?: number;
}

export interface RAGContentRequest {
  requestId: string;
  documentId: string;
}

export interface RAGDeleteDocumentRequest {
  requestId: string;
  documentId: string;
}

export interface RAGIngestResponse {
  success: boolean;
  message: string;
  document_id: string;
  filename: string;
  file_path: string;
  file_size: number;
  file_description: string;
  file_abstract: string;
  collection_type: string;
  classification_mode: string;
}

export interface RAGListResponse {
  success: boolean;
  documents: RAGDocument[];
  total: number;
  requestId: string;
}

export interface RAGContentResponse {
  success: boolean;
  document_id: string;
  filename: string;
  content: string;
  file_size: number;
  requestId: string;
}

export interface RAGDeleteDocumentResponse {
  success: boolean;
  message: string;
  requestId: string;
}

// RAG API服务
export const ragApi = {
  // 上传文档（通过文件路径）
  ingestByPath: (data: RAGIngestRequest): Promise<RAGIngestResponse> =>
    ragRequest.post('/ingest', data),

  // 上传文档（通过文本内容）
  ingestByContent: (data: RAGIngestRequest): Promise<RAGIngestResponse> =>
    ragRequest.post('/ingest', data),

  // 获取文档列表
  listDocuments: (data: RAGListRequest): Promise<RAGListResponse> =>
    ragRequest.post('/list', data),

  // 获取文档内容
  getDocumentContent: (data: RAGContentRequest): Promise<RAGContentResponse> =>
    ragRequest.post('/content', data),

  // 删除单个文档
  deleteDocument: (data: RAGDeleteDocumentRequest): Promise<RAGDeleteDocumentResponse> =>
    ragRequest.post('/delete-document', data),

  // 健康检查
  healthCheck: () =>
    ragRequest.get('/health'),

  // 获取状态
  getStatus: () =>
    ragRequest.get('/status'),
};

export default ragApi;
