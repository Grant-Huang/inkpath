'use client';

import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { X, Copy, Check } from 'lucide-react';

interface MarkdownPreviewProps {
  content: string;
  title?: string;
  onClose?: () => void;
}

export default function MarkdownPreview({ 
  content, 
  title,
  onClose 
}: MarkdownPreviewProps) {
  const [copied, setCopied] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('复制失败:', err);
    }
  };

  if (!mounted) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-2/3"></div>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* 操作按钮 */}
      <div className="absolute -top-2 -right-2 flex items-center gap-1">
        <button
          onClick={handleCopy}
          className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          title="复制内容"
        >
          {copied ? (
            <Check className="w-4 h-4 text-green-500" />
          ) : (
            <Copy className="w-4 h-4 text-gray-500" />
          )}
        </button>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            title="关闭"
          >
            <X className="w-4 h-4 text-gray-500" />
          </button>
        )}
      </div>

      {/* Markdown 内容 */}
      <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-a:text-indigo-600 prose-code:text-indigo-600 prose-code:bg-indigo-50 prose-code:px-1 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  );
}

// 简单的 Markdown 渲染器（不需要额外依赖）
export function SimpleMarkdown({ content }: { content: string }) {
  // 处理 YAML front matter
  const frontMatterRegex = /^---\n[\s\S]*?\n---\n/;
  const cleanContent = content.replace(frontMatterRegex, '');
  
  // 基本 Markdown 转换
  const lines = cleanContent.split('\n');
  const elements: React.ReactNode[] = [];
  let inList = false;
  let listItems: React.ReactNode[] = [];

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="list-disc list-inside ml-4 space-y-1">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  lines.forEach((line, index) => {
    // 跳过空行
    if (!line.trim()) {
      flushList();
      return;
    }

    // 标题
    if (line.startsWith('# ')) {
      flushList();
      elements.push(
        <h1 key={index} className="text-2xl font-bold mt-6 mb-4">
          {line.substring(2)}
        </h1>
      );
    } else if (line.startsWith('## ')) {
      flushList();
      elements.push(
        <h2 key={index} className="text-xl font-bold mt-5 mb-3">
          {line.substring(3)}
        </h2>
      );
    } else if (line.startsWith('### ')) {
      flushList();
      elements.push(
        <h3 key={index} className="text-lg font-semibold mt-4 mb-2">
          {line.substring(4)}
        </h3>
      );
    } 
    // 列表
    else if (line.startsWith('- ') || line.startsWith('* ')) {
      inList = true;
      listItems.push(
        <span key={index}>{line.substring(2)}</span>
      );
    }
    // 引用
    else if (line.startsWith('> ')) {
      flushList();
      elements.push(
        <blockquote key={index} className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-4">
          {line.substring(2)}
        </blockquote>
      );
    }
    // 代码块
    else if (line.startsWith('```')) {
      flushList();
      elements.push(
        <pre key={index} className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4 font-mono text-sm">
          <code>{line.substring(3)}</code>
        </pre>
      );
    }
    // 分隔线
    else if (line.match(/^[-*_]{3,}$/)) {
      flushList();
      elements.push(<hr key={index} className="my-6 border-gray-300" />);
    }
    // 普通段落
    else {
      flushList();
      // 处理行内格式
      let text = line;
      
      // 加粗 **text**
      text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      // 斜体 *text*
      text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
      // 行内代码 `code`
      text = text.replace(/`(.+?)`/g, '<code class="bg-gray-100 px-1 rounded text-sm">$1</code>');
      // 链接 [text](url)
      text = text.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" class="text-indigo-600 hover:underline">$1</a>');
      
      elements.push(
        <p key={index} className="mb-3 leading-relaxed" dangerouslySetInnerHTML={{ __html: text }} />
      );
    }
  });

  flushList();

  return <div className="space-y-2">{elements}</div>;
}
