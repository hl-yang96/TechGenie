import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Empty, Tooltip, Modal, Button, message } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import { useMemoizedFn } from 'ahooks';
import classNames from 'classnames';
import { sessionApi, ChatSessionInfo } from '@/services/session';
import { fileApi } from '@/services/file';
import { formatTimestamp } from '@/utils';

interface ChatHistoryProps {
  className?: string;
  currentReqId?: string;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({
  className,
  currentReqId
}) => {
  const navigate = useNavigate();
  const [modal, contextHolder] = Modal.useModal();
  const [sessions, setSessions] = useState<ChatSessionInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);

  // 加载历史会话列表
  const loadSessions = useMemoizedFn(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await sessionApi.listSessions({ limit: 50, offset: 0 });

      if (response.success) {
        setSessions(response.sessions);
      } else {
        setError(response.message || '获取历史会话失败');
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
      setError('获取历史会话失败，请检查后端服务是否运行');
    } finally {
      setLoading(false);
    }
  });

  // 处理会话点击 - 跳转到session页面
  const handleSessionClick = useMemoizedFn((session: ChatSessionInfo) => {
    // 跳转到对应的session页面，添加from=history参数
    navigate(`/${session.reqId}?from=history`);
  });

  // 处理删除会话
  const handleDeleteSession = async (session: ChatSessionInfo, event: React.MouseEvent) => {
    event.stopPropagation(); // 阻止事件冒泡，避免触发会话点击

    console.log('Delete button clicked for session:', session.reqId);

    // 先测试一个简单的确认框
    modal.confirm({
      title: '确认删除',
      content: `确定要删除会话 "${session.chatTitle || '未命名对话'}" 吗？`,
      okText: '确定删除',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        console.log('User confirmed delete');
        try {
          setDeletingSessionId(session.reqId);
          const response = await sessionApi.deleteSession({ reqId: session.reqId });
          if (response.success) {
            setSessions(prev => prev.filter(s => s.reqId !== session.reqId));
            message.success('会话删除成功');
          } else {
            message.error(response.message || '删除失败');
          }
        } catch (deleteErr) {
          console.error('Failed to delete session:', deleteErr);
          message.error('删除失败，请重试');
        } finally {
          setDeletingSessionId(null);
        }
      },
      onCancel: () => {
        console.log('Delete cancelled by user');
      }
    });
  };



  // 组件挂载时加载数据
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // 渲染会话项
  const renderSessionItem = (session: ChatSessionInfo) => {
    const isActive = currentReqId === session.reqId;
    // 直接使用chatTitle作为显示标题，后端已经处理了从query提取标题的逻辑
    const displayTitle = session.chatTitle || '未命名对话';
    const createdTime = formatTimestamp(new Date(session.createdAt).getTime());
    const isDeleting = deletingSessionId === session.reqId;

    return (
      <div
        key={session.reqId}
        className={classNames(
          'p-12 cursor-pointer border-b border-gray-100 hover:bg-gray-50 transition-colors group',
          {
            'bg-blue-50 border-blue-200': isActive,
            'opacity-50': isDeleting,
          }
        )}
        onClick={() => handleSessionClick(session)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <Tooltip title={displayTitle} placement="right">
              <div className="text-sm font-medium text-gray-900 truncate mb-4">
                {displayTitle}
              </div>
            </Tooltip>
            <div className="text-xs text-gray-500">
              {createdTime}
            </div>
          </div>

          {/* 删除按钮 */}
          <div className="ml-8 opacity-0 group-hover:opacity-100 transition-opacity">
            <Tooltip title="删除会话">
              <Button
                type="text"
                size="small"
                loading={isDeleting}
                icon={<DeleteOutlined />}
                onClick={(e) => handleDeleteSession(session, e)}
                className="text-gray-400 hover:text-red-500 flex-shrink-0"
                disabled={isDeleting}
              />
            </Tooltip>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={classNames('h-full flex flex-col bg-white', className)}>
      {contextHolder}
      {/* 标题栏 */}
      <div className="p-16 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">历史对话</h3>
          <Tooltip title="刷新">
            <i
              className="font_family icon-shuaxin cursor-pointer text-gray-500 hover:text-gray-700"
              onClick={loadSessions}
            />
          </Tooltip>
        </div>
      </div>

      {/* 会话列表 */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="p-16 text-center text-gray-500">
            加载中...
          </div>
        )}
        
        {error && (
          <div className="p-16 text-center text-red-500">
            {error}
          </div>
        )}
        
        {!loading && !error && sessions.length === 0 && (
          <div className="p-16">
            <Empty 
              description="暂无历史对话"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          </div>
        )}
        
        {!loading && !error && sessions.length > 0 && (
          <div>
            {sessions.map(renderSessionItem)}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatHistory;
