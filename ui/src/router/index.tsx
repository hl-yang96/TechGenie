import React, { Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import Layout from '@/layout/index';
import { Loading } from '@/components';

// 使用常量存储路由路径
const ROUTES = {
  HOME: '/',
  CHAT: '/:requestId',
  HISTORY: '/history',
  RAG_DOCUMENTS: '/rag_documents',
  PROJECT_MANAGEMENT: '/project_management',
  NOT_FOUND: '*',
};

// 使用 React.lazy 懒加载组件
const Home = React.lazy(() => import('@/pages/Home'));
const History = React.lazy(() => import('@/pages/History'));
const RAGDocuments = React.lazy(() => import('@/pages/RAGDocuments'));
const ProjectManagement = React.lazy(() => import('@/pages/ProjectManagement'));
const NotFound = React.lazy(() => import('@/components/NotFound'));

// 创建路由配置
const router = createBrowserRouter([
  {
    path: ROUTES.HOME,
    element: <Layout />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<Loading loading={true} className="h-full"/>}>
            <Home />
          </Suspense>
        ),
      },
      {
        path: ROUTES.CHAT,
        element: (
          <Suspense fallback={<Loading loading={true} className="h-full"/>}>
            <Home />
          </Suspense>
        ),
      },
      {
        path: ROUTES.HISTORY,
        element: (
          <Suspense fallback={<Loading loading={true} className="h-full"/>}>
            <History />
          </Suspense>
        ),
      },
      {
        path: ROUTES.RAG_DOCUMENTS,
        element: (
          <Suspense fallback={<Loading loading={true} className="h-full"/>}>
            <RAGDocuments />
          </Suspense>
        ),
      },
      {
        path: ROUTES.PROJECT_MANAGEMENT,
        element: (
          <Suspense fallback={<Loading loading={true} className="h-full"/>}>
            <ProjectManagement />
          </Suspense>
        ),
      },
      {
        path: ROUTES.NOT_FOUND,
        element: (
          <Suspense fallback={<Loading loading={true} className="h-full"/>}>
            <NotFound />
          </Suspense>
        ),
      },
    ],
  },
  // 重定向所有未匹配的路由到 404 页面
  {
    path: '*',
    element: <Navigate to={ROUTES.NOT_FOUND} replace />,
  },
]);

export default router;
