import { memo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from 'antd';
import { FolderOpenOutlined, CodeOutlined, HistoryOutlined } from '@ant-design/icons';
import Lottie from 'react-lottie';
import { animationData } from '../Slogn/animation';

const Header: GenieType.FC = memo(() => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleRAGManagement = () => {
    navigate('/rag_documents');
  };

  const handleProjectManagement = () => {
    navigate('/project_management');
  };

  const handleHistory = () => {
    navigate('/history');
  };

  const handleHome = () => {
    console.log('Header: handleHome clicked, navigating to /');
    navigate('/');
  };

  const lottieOptions = {
    loop: true,
    autoplay: true,
    animationData: animationData,
    rendererSettings: {
      preserveAspectRatio: 'xMidYMid slice',
    },
  };

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-[#E9E9F0] px-24 py-8 shadow-[0_2px_8px_0_rgba(198,202,240,0.1)]">
      <div className="flex justify-between items-center max-w-[1200px] mx-auto">
        {/* Logo/Title */}
        <div className="flex items-center space-x-16">
          <div
            className="flex items-center cursor-pointer hover:opacity-80 transition-opacity duration-200"
            onClick={handleHome}
          >
            <Lottie
              options={lottieOptions}
              height={32}
              width={120}
            />
          </div>

          {/* 历史对话按钮 - 放在logo右侧 */}
          <Button
            type="default"
            icon={<HistoryOutlined />}
            onClick={handleHistory}
            className="!h-[40px] !px-16 !rounded-xl !border-[#E9E9F0] !text-[#4040FF] hover:!border-[#4040FF] hover:!bg-[rgba(64,64,255,0.02)] !font-medium flex items-center"
          >
            历史对话
          </Button>
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center space-x-16">
          {location.pathname === '/' && (
            <>
              <Button
                type="default"
                icon={<FolderOpenOutlined />}
                onClick={handleRAGManagement}
                className="!h-[40px] !px-16 !rounded-xl !border-[#E9E9F0] !text-[#4040FF] hover:!border-[#4040FF] hover:!bg-[rgba(64,64,255,0.02)] !font-medium flex items-center"
              >
                RAG文档管理
              </Button>
              <Button
                type="default"
                icon={<CodeOutlined />}
                onClick={handleProjectManagement}
                className="!h-[40px] !px-16 !rounded-xl !border-[#E9E9F0] !text-[#4040FF] hover:!border-[#4040FF] hover:!bg-[rgba(64,64,255,0.02)] !font-medium flex items-center"
              >
                代码库管理
              </Button>
            </>
          )}

          {(location.pathname === '/rag_documents' || location.pathname === '/project_management' || location.pathname === '/history') && (
            <Button
              type="default"
              onClick={handleHome}
              className="!h-[40px] !px-16 !rounded-xl !border-[#E9E9F0] !text-[#666] hover:!border-[#4040FF] hover:!text-[#4040FF] hover:!bg-[rgba(64,64,255,0.02)] !font-medium flex items-center"
            >
              返回主页
            </Button>
          )}
        </div>
      </div>
    </div>
  );
});

Header.displayName = 'Header';

export default Header;
