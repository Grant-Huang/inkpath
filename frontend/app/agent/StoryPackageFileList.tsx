'use client';

import React from 'react';
import { FileText, Eye, CheckCircle, Clock, AlertCircle } from 'lucide-react';

interface FileInfo {
  name: string;
  content: string;
}

interface StoryPackageFileListProps {
  files: FileInfo[];
  status: 'incomplete' | 'complete' | 'submitted';
  onPreview: (file: FileInfo) => void;
}

export default function StoryPackageFileList({
  files,
  status,
  onPreview,
}: StoryPackageFileListProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'complete':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'incomplete':
        return <Clock className="w-4 h-4 text-amber-500" />;
      case 'submitted':
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'complete':
        return '故事包已完成';
      case 'incomplete':
        return '故事包完善中';
      case 'submitted':
        return '已提交到 InkPath';
    }
  };

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-3 py-2 bg-gray-100 border-b flex items-center justify-between">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className="text-sm font-medium text-gray-700">
            {getStatusText()}
          </span>
        </div>
        <span className="text-xs text-gray-500">
          {files.length} 个文件
        </span>
      </div>
      
      <div className="divide-y">
        {files.map((file, index) => (
          <div
            key={index}
            className="px-3 py-2 flex items-center justify-between hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-700">
                {file.name}
              </span>
            </div>
            <button
              onClick={() => onPreview(file)}
              className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-700"
            >
              <Eye className="w-3 h-3" />
              预览
            </button>
          </div>
        ))}
      </div>
      
      {status === 'incomplete' && (
        <div className="px-3 py-2 bg-amber-50 text-amber-700 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          请继续完善故事信息
        </div>
      )}
    </div>
  );
}
