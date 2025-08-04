import React, { useState, useEffect, useCallback } from 'react';
import {
  Typography,
  Button,
  Input,
  Form,
  message,
  Spin,
  Empty,
  Popconfirm
} from 'antd';
import {
  CodeOutlined,
  PlusOutlined,
  DeleteOutlined,
  ReloadOutlined,
  FolderOpenOutlined
} from '@ant-design/icons';
import { projectApi, ProjectInfo } from '@/services/project';
import { ProjectDescription } from '@/components';

const { Title, Text } = Typography;
const { TextArea } = Input;

// 表单数据接口
interface ProjectFormData {
  name: string;
  path: string;
  description?: string;
}

const ProjectManagement: React.FC = () => {
  const [form] = Form.useForm();
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [selectedProject, setSelectedProject] = useState<ProjectInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // 获取项目列表
  const fetchProjects = useCallback(async () => {
    setLoading(true);
    try {
      const response = await projectApi.listProjects({});
      if (response.success) {
        setProjects(response.projects);
      } else {
        message.error('获取项目列表失败');
      }
    } catch (error) {
      console.error('获取项目列表失败:', error);
      message.error(`获取项目列表失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // 创建项目
  const handleCreateProject = async (values: ProjectFormData) => {
    setSubmitting(true);
    try {
      const response = await projectApi.createProject(values);
      if (response.success) {
        message.success('项目导入成功');
        form.resetFields();
        fetchProjects();
      } else {
        message.error(response.message || '项目导入失败');
      }
    } catch (error) {
      console.error('创建项目失败:', error);
      message.error(`项目导入失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setSubmitting(false);
    }
  };

  // 删除项目
  const handleDeleteProject = async (projectId: number) => {
    try {
      const response = await projectApi.deleteProject({ project_id: projectId });
      if (response.success) {
        message.success('项目删除成功');
        if (selectedProject?.id === projectId) {
          setSelectedProject(null);
        }
        fetchProjects();
      } else {
        message.error(response.message || '项目删除失败');
      }
    } catch (error) {
      console.error('删除项目失败:', error);
      message.error(`项目删除失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  // 选择项目
  const handleProjectSelect = (project: ProjectInfo) => {
    setSelectedProject(project);
  };

  // 回到添加项目页面
  const handleBackToAdd = () => {
    setSelectedProject(null);
  };

  // 初始化加载
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-[1200px] mx-auto px-24 py-32">
        {/* 页面标题区域 */}
        <div className="text-center mb-32">
          <div className="flex items-center justify-center mb-16">
            <CodeOutlined className="text-[32px] text-[#4040FF] mr-12" />
            <Title level={1} className="!mb-0 !text-[32px] !font-bold">代码库管理</Title>
          </div>
          <Text className="text-[16px] text-[#666] leading-[24px]">
            管理您的项目代码库，快速导入和组织项目路径
          </Text>
        </div>

        {/* 主要内容区域 */}
        <div className="grid grid-cols-4 gap-24">
          {/* 左侧：项目列表 Sidebar */}
          <div className="col-span-1">
            <div className="bg-white rounded-xl border border-[#E9E9F0] p-20 shadow-[0_8px_20px_0_rgba(198,202,240,0.1)] sticky top-[100px] h-[calc(100vh-120px)] flex flex-col">
              <div className="flex items-center justify-between mb-20">
                <div className="flex items-center">
                  <FolderOpenOutlined className="text-[16px] text-[#4040FF] mr-8" />
                  <Title level={4} className="!mb-0 !text-[16px]">项目列表</Title>
                </div>
                <div className="flex items-center gap-8">
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={handleBackToAdd}
                    size="small"
                    className="!bg-[#4040FF] hover:!bg-[#3030EE] !border-[#4040FF] hover:!border-[#3030EE]"
                    title="添加新项目"
                  />
                  <Button
                    type="text"
                    icon={<ReloadOutlined />}
                    onClick={fetchProjects}
                    loading={loading}
                    size="small"
                    className="!text-[#4040FF] hover:!bg-[rgba(64,64,255,0.1)]"
                  />
                </div>
              </div>

              <div className="flex-1 overflow-y-auto">
                {loading ? (
                  <div className="flex justify-center items-center h-[200px]">
                    <Spin size="large" />
                  </div>
                ) : projects.length === 0 ? (
                  <Empty 
                    description="暂无项目"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    className="!my-40"
                  />
                ) : (
                  <div className="space-y-4">
                    {projects.map((project) => {
                      // 提取用户描述部分
                      const getUserDescription = (description: string) => {
                        if (!description) return '';
                        const match = description.match(/### 用户描述:\s*\n(.*?)(?:\n### 代码分析助手:|$)/s);
                        return match ? match[1].trim() : '';
                      };

                      const userDescription = getUserDescription(project.description || '');

                      return (
                        <div
                          key={project.id}
                          onClick={() => handleProjectSelect(project)}
                          className={`p-8 rounded-lg border cursor-pointer transition-all duration-200 ${
                            selectedProject?.id === project.id
                              ? 'border-[#4040FF] bg-[rgba(64,64,255,0.02)]'
                              : 'border-[#E9E9F0] hover:border-[#4040FF] hover:bg-[rgba(64,64,255,0.02)]'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-4">
                            <Text strong className="text-[14px] truncate flex-1 mr-8">
                              {project.name}
                            </Text>
                            <Popconfirm
                              title="确认删除"
                              description="确定要删除这个项目吗？"
                              onConfirm={(e) => {
                                e?.stopPropagation();
                                handleDeleteProject(project.id);
                              }}
                              okText="确认"
                              cancelText="取消"
                            >
                              <Button
                                type="text"
                                icon={<DeleteOutlined />}
                                size="small"
                                className="!text-[#ff4d4f] hover:!bg-[rgba(255,77,79,0.1)]"
                                onClick={(e) => e.stopPropagation()}
                              />
                            </Popconfirm>
                          </div>
                          {userDescription && (
                            <Text className="text-[12px] text-[#666] block truncate">
                              {userDescription}
                            </Text>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 右侧：项目详情/创建表单 */}
          <div className="col-span-3">
            <div className="bg-white rounded-xl border border-[#E9E9F0] p-32 shadow-[0_8px_20px_0_rgba(198,202,240,0.1)]">
              {selectedProject ? (
                // 显示选中项目的详情
                <div>
                  <Title level={3} className="!mb-24 !text-[24px]">项目详情</Title>
                  <div className="space-y-20">
                    <div>
                      <Text strong className="text-[16px] text-[#333]">项目名称：</Text>
                      <Text className="text-[16px] text-[#666] ml-8">{selectedProject.name}</Text>
                    </div>
                    <div>
                      <Text strong className="text-[16px] text-[#333]">项目路径：</Text>
                      <Text className="text-[14px] text-[#666] ml-8 font-mono bg-[#f5f5f5] px-8 py-4 rounded">
                        {selectedProject.path}
                      </Text>
                    </div>
                    <div>
                      <Text strong className="text-[16px] text-[#333]">项目描述：</Text>
                      <div className="mt-8 pt-16 pb-16 px-16 bg-[#f8f9fa] rounded-lg border border-[#E9E9F0]">
                        <ProjectDescription
                          description={selectedProject.description || ''}
                          className="text-[14px] text-[#666] leading-[20px]"
                        />
                      </div>
                    </div>
                    <div>
                      <Text strong className="text-[16px] text-[#333]">创建时间：</Text>
                      <Text className="text-[16px] text-[#666] ml-8">
                        {new Date(selectedProject.created_at).toLocaleString()}
                      </Text>
                    </div>
                  </div>
                </div>
              ) : (
                // 显示创建项目表单
                <div>
                  <Title level={3} className="!mb-24 !text-[24px]">导入新项目</Title>
                  <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleCreateProject}
                    className="space-y-20"
                  >
                    <Form.Item
                      name="name"
                      label={<Text strong className="text-[16px]">项目名称</Text>}
                      rules={[
                        { required: true, message: '请输入项目名称' },
                        { max: 100, message: '项目名称不能超过100个字符' }
                      ]}
                    >
                      <Input 
                        placeholder="请输入项目名称"
                        className="!h-[44px] !text-[16px]"
                      />
                    </Form.Item>

                    <Form.Item
                      name="path"
                      label={<Text strong className="text-[16px]">项目绝对路径</Text>}
                      rules={[
                        { required: true, message: '请输入项目绝对路径' }
                      ]}
                    >
                      <Input 
                        placeholder="请输入项目的绝对路径，如：/Users/username/projects/myproject"
                        className="!h-[44px] !text-[16px] font-mono"
                      />
                    </Form.Item>

                    <Form.Item
                      name="description"
                      label={<Text strong className="text-[16px]">项目描述</Text>}
                      rules={[
                        { max: 500, message: '项目描述不超过500个字符' }
                      ]}
                    >
                      <TextArea 
                        placeholder="请输入简短的项目介绍"
                        rows={3}
                        maxLength={500}
                        showCount
                        className="!text-[16px]"
                      />
                    </Form.Item>

                    <Form.Item className="!mb-0 !mt-32">
                      <Button
                        type="primary"
                        htmlType="submit"
                        loading={submitting}
                        icon={<PlusOutlined />}
                        className="!h-[44px] !px-32 !text-[16px] !font-medium !bg-[#4040FF] hover:!bg-[#3030EE]"
                      >
                        导入项目
                      </Button>
                    </Form.Item>
                  </Form>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectManagement;
