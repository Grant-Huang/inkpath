import { NextRequest, NextResponse } from 'next/server';
import { LLMClient } from '@/lib/llm';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { content, style } = body;

    if (!content) {
      return NextResponse.json({ error: '内容不能为空' }, { status: 400 });
    }

    const llm = new LLMClient();
    
    const prompt = `请润色以下故事内容，使其更加流畅、生动：

## 原文
${content}

## 要求
1. 保持原文的风格和意图
2. 修改病句、用词不当
3. 增加适当的描写
4. 保持克制、冷峻的基调
5. 不要改变故事的核心情节

请直接输出润色后的内容，不需要任何解释。`;

    const polished = await llm.generate(prompt, {
      maxTokens: 1500,
      temperature: 0.6
    });

    return NextResponse.json({ content: polished });
  } catch (error) {
    console.error('AI polish error:', error);
    return NextResponse.json({ error: '润色失败' }, { status: 500 });
  }
}
