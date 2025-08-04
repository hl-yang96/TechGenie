import React from 'react';
import ChatHistory from '@/components/ChatHistory';

const HistoryPage: React.FC = () => {
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* 主要内容区域 */}
      <div className="flex-1 flex justify-center py-24">
        <div className="w-full max-w-[800px] bg-white rounded-lg shadow-sm border border-gray-200">
          <ChatHistory
            className="h-full"
          />
        </div>
      </div>
    </div>
  );
};

export default HistoryPage;
