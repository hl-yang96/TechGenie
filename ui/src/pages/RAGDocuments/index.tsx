import { useState, useEffect, useCallback, memo, useRef } from 'react';
import {
  Button,
  Input,
  message,
  Spin,
  Typography,
  Tag,
  Empty,
  Pagination
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  ReloadOutlined,
  CloudUploadOutlined,
  EditOutlined,
  FolderOpenOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { ragApi, type RAGDocument } from '@/services/rag';
import './index.css';

const { TextArea } = Input;
const { Title, Text } = Typography;

type RAGDocumentsProps = Record<string, never>;

const RAGDocuments: GenieType.FC<RAGDocumentsProps> = memo(() => {
  const [documents, setDocuments] = useState<RAGDocument[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalDocuments, setTotalDocuments] = useState(0);
  const pageSize = 10;
  const [uploading, setUploading] = useState(false);
  const [textContent, setTextContent] = useState('');
  const [selectedDocument, setSelectedDocument] = useState<RAGDocument | null>(null);
  const [documentContent, setDocumentContent] = useState<string>('');
  const [statusInfo, setStatusInfo] = useState<any>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePath, setFilePath] = useState<string>('');

  // 文件输入引用
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 生成请求ID
  const generateRequestId = () => `rag_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;

  // 获取文档列表
  const fetchDocuments = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const response = await ragApi.listDocuments({
        requestId: generateRequestId(),
        limit: pageSize,
        offset: (page - 1) * pageSize
      });

      if (response.success) {
        setDocuments(response.documents);
        setTotalDocuments(response.total || 0);
        setCurrentPage(page);
      } else {
        message.error('获取文档列表失败');
      }
    } catch (error) {
      console.error('获取文档列表失败:', error);
      message.error(`获取文档列表失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setLoading(false);
    }
  }, [pageSize]);

  // 处理分页变化
  const handlePageChange = (page: number) => {
    fetchDocuments(page);
  };

  // 获取状态信息
  const fetchStatus = useCallback(async () => {
    try {
      const response = await ragApi.getStatus();
      setStatusInfo(response);
    } catch (error) {
      console.error('获取状态信息失败:', error);
    }
  }, []);

  // 页面加载时获取文档列表和状态信息
  useEffect(() => {
    fetchDocuments(1);
    fetchStatus();
  }, [fetchStatus]);

  // 处理文件选择 - 使用浏览器文件选择器
  const handleFileSelect = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // 处理文件输入变化
  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);

      // 尝试获取文件的完整路径
      // 注意：在现代浏览器中，出于安全考虑，无法直接获取文件的绝对路径
      // 我们使用文件名作为路径，或者如果有 webkitRelativePath 则使用它
      const fullPath = (file as any).webkitRelativePath || file.name;
      setFilePath(fullPath);

      console.log('Selected file:', file.name);
      console.log('File path:', fullPath);
    }

    // 清空input值，允许重复选择同一文件
    event.target.value = '';
  };

  // 读取文件内容
  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result;
        if (typeof result === 'string') {
          resolve(result);
        } else if (result instanceof ArrayBuffer) {
          // 对于二进制文件，转换为 base64
          const uint8Array = new Uint8Array(result);
          const binaryString = Array.from(uint8Array, byte => String.fromCharCode(byte)).join('');
          const base64String = btoa(binaryString);
          resolve(base64String);
        } else {
          reject(new Error('无法读取文件内容'));
        }
      };
      reader.onerror = () => {
        reject(new Error('文件读取失败'));
      };

      // 根据文件类型选择读取方式
      const fileExtension = file.name.split('.').pop()?.toLowerCase();
      const textExtensions = ['txt', 'md', 'html', 'json', 'xml', 'csv'];

      if (textExtensions.includes(fileExtension || '')) {
        reader.readAsText(file, 'UTF-8');
      } else {
        // 对于 PDF、Word 等二进制文件，读取为 ArrayBuffer
        reader.readAsArrayBuffer(file);
      }
    });
  };




  // 处理文件上传
  const handleFileUpload = async () => {
    if (!selectedFile) {
      message.warning('请先选择文件');
      return;
    }

    setUploading(true);
    try {
      // 读取文件内容
      const fileContent = await readFileContent(selectedFile);

      // 使用从文件选择器获取的路径
      const pathToUse = filePath || selectedFile.name;

      console.log('Uploading file with path:', pathToUse);
      console.log('File content length:', fileContent.length);

      // 同时发送文件路径和内容
      const response = await ragApi.ingestByPath({
        requestId: generateRequestId(),
        documentPath: pathToUse,
        documentContent: fileContent,
      });

      if (response.success) {
        message.success(`文件 "${response.filename}" 上传成功！`);
        setSelectedFile(null);
        setFilePath('');
        fetchDocuments(currentPage);
        fetchStatus();
      } else {
        message.error('文件上传失败');
      }
    } catch (error) {
      console.error('文件上传失败:', error);
      message.error(`文件上传失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setUploading(false);
    }
  };

  // 处理文本上传
  const handleTextUpload = async () => {
    if (!textContent.trim()) {
      message.warning('请输入要上传的文本内容');
      return;
    }

    setUploading(true);
    try {
      const response = await ragApi.ingestByContent({
        requestId: generateRequestId(),
        documentContent: textContent,
      });

      if (response.success) {
        message.success(`文档 "${response.filename}" 上传成功！`);
        setTextContent('');
        fetchDocuments(currentPage);
        fetchStatus();
      } else {
        message.error('文本上传失败');
      }
    } catch (error) {
      console.error('文本上传失败:', error);
      message.error(`文本上传失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setUploading(false);
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 格式化日期
  const formatDate = (dateString?: string) => {
    if (!dateString) return '未知';
    return new Date(dateString).toLocaleString('zh-CN');
  };

  // 处理文档选择
  const handleDocumentSelect = async (doc: RAGDocument) => {
    setSelectedDocument(doc);
    setLoading(true);
    setDocumentContent('正在加载文档内容...');

    try {
      const response = await ragApi.getDocumentContent({
        requestId: generateRequestId(),
        documentId: doc.document_id
      });

      if (response.success) {
        setDocumentContent(response.content);
      } else {
        setDocumentContent('获取文档内容失败');
        message.error('获取文档内容失败');
      }
    } catch (error) {
      console.error('获取文档内容失败:', error);
      const fallbackContent = doc.file_abstract || doc.file_description || '无法获取文档内容';
      setDocumentContent(fallbackContent);
      message.error(`获取文档内容失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setLoading(false);
    }
  };

  // 清除文档选择
  const clearDocumentSelection = () => {
    setSelectedDocument(null);
    setDocumentContent('');
  };

  // 删除文档
  const handleDeleteDocument = async (document: RAGDocument) => {
    try {
      const response = await ragApi.deleteDocument({
        requestId: generateRequestId(),
        documentId: document.document_id,
      });

      if (response.success) {
        message.success(`文档 "${document.filename}" 删除成功！`);
        // 如果删除的是当前选中的文档，清除选择
        if (selectedDocument?.document_id === document.document_id) {
          clearDocumentSelection();
        }
        // 刷新文档列表
        fetchDocuments(currentPage);
        fetchStatus();
      } else {
        message.error('文档删除失败');
      }
    } catch (error) {
      console.error('文档删除失败:', error);
      message.error(`文档删除失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-[1200px] mx-auto px-24 py-32">
        {/* 页面标题区域 */}
        <div className="text-center mb-32">
          <div className="flex items-center justify-center mb-16">
            <FolderOpenOutlined className="text-[32px] text-[#4040FF] mr-12" />
            <Title level={1} className="!mb-0 !text-[32px] !font-bold">RAG文档管理</Title>
          </div>
          <Text className="text-[16px] text-[#666] leading-[24px]">
            智能文档管理系统，支持多种格式文档上传与向量化处理
          </Text>
        </div>

        {/* 统计信息区域 */}
        {statusInfo && (
          <div className="bg-white rounded-xl border border-[#E9E9F0] p-24 mb-32 shadow-[0_8px_20px_0_rgba(198,202,240,0.1)]">
            <Title level={4} className="!mb-16 !text-[18px] flex items-center">
              <span className="w-[4px] h-[18px] bg-[#4040FF] rounded mr-8"></span>
              系统状态
            </Title>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-16">
              <div className="text-center p-16 bg-[rgba(64,64,255,0.02)] rounded-xl border border-[rgba(64,64,255,0.1)]">
                <div className="text-[24px] font-bold text-[#4040FF] mb-4">
                  {documents.length}
                </div>
                <div className="text-[14px] text-[#666]">总文档数</div>
              </div>
              <div className="text-center p-16 bg-[rgba(41,204,41,0.02)] rounded-xl border border-[rgba(41,204,41,0.1)]">
                <div className="text-[24px] font-bold text-[#29CC29] mb-4">
                  {statusInfo.availableCollections?.length || 0}
                </div>
                <div className="text-[14px] text-[#666]">集合数量</div>
              </div>
              <div className="text-center p-16 bg-[rgba(255,134,13,0.02)] rounded-xl border border-[rgba(255,134,13,0.1)]">
                <div className="text-[24px] font-bold text-[#FF860D] mb-4">
                  {statusInfo.collectionStats?.collections ? Object.values(statusInfo.collectionStats.collections).reduce((sum: number, stat: any) => sum + (stat.count || 0), 0) : 0}
                </div>
                <div className="text-[14px] text-[#666]">向量块数</div>
              </div>
              <div className="text-center p-16 bg-[rgba(255,51,51,0.02)] rounded-xl border border-[rgba(255,51,51,0.1)]">
                <div className="text-[24px] font-bold text-[#FF3333] mb-4">
                  {statusInfo.isReady ? '正常' : '异常'}
                </div>
                <div className="text-[14px] text-[#666]">系统状态</div>
              </div>
            </div>
          </div>
        )}

        {/* 主要内容区域 */}
        <div className="grid grid-cols-4 gap-24">
          {/* 左侧：文档列表 Sidebar */}
          <div className="col-span-1">
            <div className="bg-white rounded-xl border border-[#E9E9F0] p-20 shadow-[0_8px_20px_0_rgba(198,202,240,0.1)] sticky top-[100px] h-[calc(100vh-120px)] flex flex-col">
              <div className="flex items-center justify-between mb-20">
                <div className="flex items-center">
                  <FileTextOutlined className="text-[16px] text-[#4040FF] mr-8" />
                  <Title level={4} className="!mb-0 !text-[16px]">文档列表</Title>
                </div>
                <Button
                  type="text"
                  icon={<ReloadOutlined />}
                  onClick={() => fetchDocuments(currentPage)}
                  loading={loading}
                  size="small"
                  className="!text-[#4040FF] hover:!bg-[rgba(64,64,255,0.1)]"
                />
              </div>

              <div className="flex-1 flex flex-col min-h-0">
                <Spin spinning={loading} className="flex-1">
                  {documents.length === 0 ? (
                    <div className="flex items-center justify-center h-full">
                      <Empty
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                        description={
                          <span className="text-[#666] text-[12px]">
                            暂无文档
                          </span>
                        }
                      />
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {documents.map((doc) => (
                        <div
                          key={doc.document_id}
                          onClick={() => handleDocumentSelect(doc)}
                          className={`document-item p-8 rounded-lg border cursor-pointer ${
                            selectedDocument?.document_id === doc.document_id
                              ? 'selected border-[#4040FF] bg-[rgba(64,64,255,0.02)]'
                              : 'border-[#E9E9F0] hover:border-[#4040FF] hover:bg-[rgba(64,64,255,0.02)]'
                          }`}
                        >
                          <Title level={5} className="!mb-4 !text-[12px] !font-medium !leading-[16px]" title={doc.filename}>
                            {doc.filename.length > 20 ? `${doc.filename.substring(0, 20)}...` : doc.filename}
                          </Title>

                          <div className="flex items-center justify-between text-[10px] text-[#999]">
                            <span>{formatFileSize(doc.file_size)}</span>
                            <Tag
                              color="#4040FF"
                              className="!text-[9px] !px-2 !py-0 !rounded-sm !leading-none"
                            >
                              {doc.collection_type}
                            </Tag>
                            <span>{formatDate(doc.created_at)?.split(' ')[0]}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </Spin>

                {/* 分页组件 */}
                {totalDocuments > 0 && (
                  <div className="mt-16 flex justify-center">
                    <Pagination
                      current={currentPage}
                      total={totalDocuments}
                      pageSize={pageSize}
                      onChange={handlePageChange}
                      showSizeChanger={false}
                      size="small"
                      className="text-[12px]"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 右侧：内容区域 */}
          <div className="col-span-3">
            {selectedDocument ? (
              /* 文档详情 */
              <div className="bg-white rounded-xl border border-[#E9E9F0] p-32 shadow-[0_8px_20px_0_rgba(198,202,240,0.1)]">
                <div className="flex items-center justify-between mb-24">
                  <div className="flex items-center">
                    <FileTextOutlined className="text-[20px] text-[#4040FF] mr-12" />
                    <Title level={3} className="!mb-0 !text-[20px]">{selectedDocument.filename}</Title>
                  </div>
                  <div className="flex items-center space-x-8">
                    <Button
                      type="text"
                      icon={<DeleteOutlined />}
                      onClick={() => handleDeleteDocument(selectedDocument)}
                      className="!text-[#ff4d4f] hover:!text-[#ff7875] hover:!bg-[rgba(255,77,79,0.1)]"
                    >
                      删除
                    </Button>
                    <Button
                      type="text"
                      onClick={clearDocumentSelection}
                      className="!text-[#666] hover:!text-[#4040FF] hover:!bg-[rgba(64,64,255,0.1)]"
                    >
                      返回上传
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-16 mb-24 p-20 bg-[rgba(64,64,255,0.02)] rounded-xl">
                  <div>
                    <Text className="text-[12px] text-[#666] block mb-4">文件大小</Text>
                    <Text className="text-[14px] font-medium">{formatFileSize(selectedDocument.file_size)}</Text>
                  </div>
                  <div>
                    <Text className="text-[12px] text-[#666] block mb-4">集合类型</Text>
                    <Tag color="#4040FF">{selectedDocument.collection_type}</Tag>
                  </div>
                  <div>
                    <Text className="text-[12px] text-[#666] block mb-4">上传时间</Text>
                    <Text className="text-[14px] font-medium">{formatDate(selectedDocument.created_at)}</Text>
                  </div>
                </div>

                {selectedDocument.file_description && (
                  <div className="mb-24">
                    <Text className="text-[14px] text-[#666] block mb-8">文档描述</Text>
                    <div className="p-16 bg-[#f8f9fa] rounded-lg border border-[#E9E9F0]">
                      <Text className="text-[14px] leading-[22px]">{selectedDocument.file_description}</Text>
                    </div>
                  </div>
                )}

                {selectedDocument.file_abstract && (
                  <div className="mb-24">
                    <Text className="text-[14px] text-[#666] block mb-8">文档摘要</Text>
                    <div className="p-16 bg-[#f8f9fa] rounded-lg border border-[#E9E9F0]">
                      <Text className="text-[14px] leading-[22px]">{selectedDocument.file_abstract}</Text>
                    </div>
                  </div>
                )}

                <div>
                  <Text className="text-[14px] text-[#666] block mb-8">文档内容预览</Text>
                  <div className="p-20 bg-[#f8f9fa] rounded-lg border border-[#E9E9F0] min-h-[300px] max-h-[500px] overflow-y-auto">
                    {loading ? (
                      <div className="flex items-center justify-center h-[200px]">
                        <Spin size="large" />
                        <Text className="ml-12 text-[14px] text-[#666]">正在加载文档内容...</Text>
                      </div>
                    ) : (
                      <Text className="text-[14px] leading-[22px] whitespace-pre-wrap">
                        {documentContent || '暂无内容'}
                      </Text>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              /* 上传区域 */
              <div className="space-y-24">
                <div className="bg-white rounded-xl border border-[#E9E9F0] p-32 shadow-[0_8px_20px_0_rgba(198,202,240,0.1)]">
                  <div className="text-center mb-24">
                    <CloudUploadOutlined className="text-[48px] text-[#4040FF] mb-16" />
                    <Title level={3} className="!mb-8 !text-[20px]">上传本地文档</Title>
                    <Text className="text-[14px] text-[#666]">
                      支持 PDF、Word、TXT、Markdown 等格式
                    </Text>
                  </div>

                  <div className="flex flex-col items-center space-y-24">
                    <div className="w-full flex justify-center">
                      {/* 文件选择器 */}
                      <div
                        className="border-2 border-dashed border-[#E9E9F0] rounded-xl p-24 text-center hover:border-[#4040FF] hover:bg-[rgba(64,64,255,0.02)] transition-all duration-300 cursor-pointer min-w-[300px]"
                        onClick={handleFileSelect}
                      >
                        <UploadOutlined className="text-[24px] text-[#4040FF] mb-12" />
                        <div className="text-[14px] font-medium text-[#333] mb-4" title={selectedFile?.name}>
                          {selectedFile
                            ? (selectedFile.name.length > 30
                                ? `${selectedFile.name.substring(0, 27)}...`
                                : selectedFile.name)
                            : '点击选择文件'
                          }
                        </div>
                        <div className="text-[12px] text-[#666]">
                          {filePath && filePath !== selectedFile?.name ? (
                            <div className="text-[#4040FF]">路径: {filePath.length > 40 ? `...${filePath.substring(filePath.length - 37)}` : filePath}</div>
                          ) : (
                            '支持格式：.txt, .md, .pdf, .doc, .docx, html, xml'
                          )}
                        </div>
                      </div>

                      {/* 隐藏的文件输入元素 */}
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".txt,.md,.pdf,.doc,.docx,.html,.xml"
                        onChange={handleFileInputChange}
                        style={{ display: 'none' }}
                      />
                    </div>

                    <Button
                      type="primary"
                      onClick={handleFileUpload}
                      loading={uploading}
                      disabled={!selectedFile}
                      size="large"
                      className={`!h-[48px] !rounded-xl !border-none !font-medium !w-[200px] ${
                        selectedFile
                          ? '!bg-[#4040FF] hover:!bg-[#3030EE] !text-white'
                          : '!bg-[#f5f5f5] !text-[#999] cursor-not-allowed'
                      }`}
                    >
                      {uploading ? '正在上传...' : '上传文件'}
                    </Button>
                  </div>
                </div>

                <div className="bg-white rounded-xl border border-[#E9E9F0] p-32 shadow-[0_8px_20px_0_rgba(198,202,240,0.1)]">
                  <div className="text-center mb-24">
                    <EditOutlined className="text-[48px] text-[#4040FF] mb-16" />
                    <Title level={3} className="!mb-8 !text-[20px]">直接输入文本</Title>
                    <Text className="text-[14px] text-[#666]">
                      粘贴或输入文本内容，快速创建文档
                    </Text>
                  </div>

                  <div className="flex flex-col items-center space-y-16">
                    <TextArea
                      value={textContent}
                      onChange={(e) => setTextContent(e.target.value)}
                      placeholder="在此输入或粘贴文本内容..."
                      rows={8}
                      maxLength={100000}
                      showCount
                      className="!border-[#E9E9F0] !rounded-xl focus:!border-[#4040FF] focus:!shadow-[0_0_0_2px_rgba(64,64,255,0.1)] w-full"
                    />
                    <Button
                      type="primary"
                      onClick={handleTextUpload}
                      loading={uploading}
                      disabled={!textContent.trim()}
                      size="large"
                      className={`!h-[48px] !rounded-xl !border-none !font-medium !w-[200px] ${
                        textContent.trim()
                          ? '!bg-[#4040FF] hover:!bg-[#3030EE] !text-white'
                          : '!bg-[#f5f5f5] !text-[#999] cursor-not-allowed'
                      }`}
                    >
                      {uploading ? '正在上传...' : '上传文本'}
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
});

RAGDocuments.displayName = 'RAGDocuments';

export default RAGDocuments;
