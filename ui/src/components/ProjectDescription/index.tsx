import React from 'react';
import { Typography } from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import classNames from 'classnames';

const { Text } = Typography;

interface ProjectDescriptionProps {
  description: string;
  className?: string;
  compact?: boolean; // 紧凑模式，用于列表显示
}

/**
 * 项目描述组件
 * 支持完整的 Markdown 格式渲染，包括粗体、斜体、列表、代码块等
 */
const ProjectDescription: React.FC<ProjectDescriptionProps> = ({
  description,
  className = "text-[14px] text-[#666]",
  compact = false
}) => {
  if (!description) {
    return (
      <Text className={className}>
        无描述
      </Text>
    );
  }

  return (
    <div className={classNames('project-description', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // 自定义段落样式
          p: ({ children }) => (
            <p className={compact ? "mb-2 leading-[16px] last:mb-0" : "mb-6 leading-[20px] last:mb-0"}>
              {children}
            </p>
          ),
          // 自定义强调文本样式
          strong: ({ children }) => (
            <strong className="font-semibold text-[#333]">{children}</strong>
          ),
          // 自定义斜体样式
          em: ({ children }) => (
            <em className="italic text-[#555]">{children}</em>
          ),
          // 自定义行内代码样式
          code: ({ children }) => (
            <code className="bg-[#f5f5f5] text-[#d73a49] px-[4px] py-[2px] rounded text-[13px] font-mono">
              {children}
            </code>
          ),
          // 自定义代码块样式
          pre: ({ children }) => (
            <pre className="bg-[#f8f8f8] border border-[#e1e4e8] rounded-[6px] p-12 my-8 overflow-x-auto text-[13px]">
              {children}
            </pre>
          ),
          // 自定义无序列表样式
          ul: ({ children }) => (
            <ul className={compact ? "list-disc list-inside mb-4 space-y-1 pl-12" : "list-disc list-inside mb-8 space-y-2 pl-16"}>
              {children}
            </ul>
          ),
          // 自定义有序列表样式
          ol: ({ children }) => (
            <ol className={compact ? "list-decimal list-inside mb-4 space-y-1 pl-12" : "list-decimal list-inside mb-8 space-y-2 pl-16"}>
              {children}
            </ol>
          ),
          // 自定义列表项样式
          li: ({ children }) => (
            <li className={compact ? "leading-[16px]" : "leading-[18px]"}>{children}</li>
          ),
          // 自定义链接样式
          a: ({ href, children }) => (
            <a
              href={href}
              className="text-[#4040FF] hover:text-[#3030EE] underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
          // 自定义标题样式
          h1: ({ children }) => (
            <h1 className="text-[16px] font-bold text-[#333] mb-8 mt-12 first:mt-0">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-[15px] font-bold text-[#333] mb-6 mt-10 first:mt-0">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-[14px] font-semibold text-[#333] mb-4 mt-8 first:mt-0">{children}</h3>
          ),
          // 自定义引用样式
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-[#dfe2e5] pl-12 my-8 text-[#6a737d] italic">
              {children}
            </blockquote>
          ),
          // 自定义分割线样式
          hr: () => (
            <hr className="border-0 border-t border-[#e1e4e8] my-12" />
          ),
        }}
      >
        {description}
      </ReactMarkdown>
    </div>
  );
};

export default ProjectDescription;
