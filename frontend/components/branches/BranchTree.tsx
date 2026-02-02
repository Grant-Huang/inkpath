'use client';

interface Branch {
  id: string;
  label: string;
  segments: number;
  bots: number;
  isMain: boolean;
  parentId: string | null;
  forkAt?: number;
}

interface BranchTreeProps {
  branches: Branch[];
  selectedBranch: string;
  onSelect: (branchId: string) => void;
  onCreateBranch: () => void;
}

export default function BranchTree({
  branches,
  selectedBranch,
  onSelect,
  onCreateBranch,
}: BranchTreeProps) {
  return (
    <div className="w-60 flex-shrink-0">
      <div className="mb-5">
        <h3 className="text-xs font-semibold text-[#a89080] uppercase tracking-wider">
          故事分支
        </h3>
      </div>
      <div className="space-y-0">
        {branches.map((branch) => {
          const isSelected = selectedBranch === branch.id;
          const indent = branch.parentId ? 32 : 0;

          return (
            <div key={branch.id} className="relative">
              {branch.parentId && (
                <div className="absolute left-4 top-0 w-4 h-1/2 border-l-2 border-b-2 border-[#d9d3ca] rounded-bl-lg pointer-events-none" />
              )}
              <div
                onClick={() => onSelect(branch.id)}
                className={`${indent > 0 ? 'ml-8' : 'ml-0'} p-2.5 rounded-lg cursor-pointer transition-all duration-150 flex items-center gap-2.5 ${
                  isSelected
                    ? 'bg-[#f0ecf7]'
                    : 'hover:bg-[#faf8f5]'
                }`}
              >
                <div
                  className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    branch.isMain
                      ? 'bg-[#6B5B95]'
                      : 'bg-[#E07A5F]'
                  } ${
                    isSelected
                      ? branch.isMain
                        ? 'shadow-[0_0_0_3px_rgba(107,91,149,0.2)]'
                        : 'shadow-[0_0_0_3px_rgba(224,122,95,0.2)]'
                      : ''
                  }`}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-sm font-${isSelected ? 'semibold' : 'medium'} ${
                        isSelected ? 'text-[#2c2420]' : 'text-[#5a4f45]'
                      }`}
                    >
                      {branch.label}
                    </span>
                    {branch.isMain && (
                      <span className="text-[9px] font-semibold text-[#6B5B95] bg-[#ebe7f5] px-1.5 py-0.5 rounded-full uppercase tracking-wide">
                        主线
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-[#a89080] mt-0.5">
                    {branch.segments} 段续写 · {branch.bots} 个 Bot
                    {branch.parentId && (
                      <span className="text-[#c4b8a8]">
                        {' '}
                        · 从第 {branch.forkAt} 段分叉
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-7 pt-5 border-t border-[#ede9e3]">
        <button
          onClick={onCreateBranch}
          className="w-full bg-transparent border-2 border-dashed border-[#d9d3ca] rounded-lg py-2 cursor-pointer text-xs text-[#a89080] transition-all duration-150 hover:border-[#E07A5F] hover:text-[#E07A5F]"
        >
          + 创建新分支
        </button>
      </div>
    </div>
  );
}
