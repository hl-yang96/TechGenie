import { memo, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { ConfigProvider, message } from 'antd';
import { ConstantProvider } from '@/hooks';
import * as constants from "@/utils/constants";
import { setMessage } from '@/utils';
import { Header } from '@/components';

// Layout 组件：应用的主要布局结构
const Layout: GenieType.FC = memo(() => {
  const [messageApi, messageContent] = message.useMessage();

  useEffect(() => {
    // 初始化全局 message
    setMessage(messageApi);
  }, [messageApi]);

  return (
    <ConfigProvider theme={{ token: { colorPrimary: '#4040FFB2' } }}>
      {messageContent}
      {/* 暂时只有静态的 */}
      <ConstantProvider value={constants}>
        <div className="min-h-screen">
          <Header />
          <div className="pt-[64px]">
            <Outlet />
          </div>
        </div>
      </ConstantProvider>
    </ConfigProvider>
  );
});

Layout.displayName = 'Layout';

export default Layout;
