import { NextRequest, NextResponse } from 'next/server';
import { LLMClient } from '@/lib/llm';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { prompt, style, language } = body;

    if (!prompt) {
      return NextResponse.json({ error: '提示词不能为空' }, { status: 400 });
    }

    const llm = new LLMClient();
    
    const systemPrompt = `你是一个专业的故事作家，擅长创作高质量的中文故事。

## 风格要求
${style || '克制,冷峻,悬念,短句为主'}

## 语言
${language || 'zh'}

## 任务
根据用户的提示生成故事内容。要求：
1. 保持故事连贯性
2. 符合指定的风格
3. 内容健康、积极
4. 字数控制在 400-500 字

请直接输出故事内容，不需要任何解释。`;

    const content = await llm.generate(`${systemPrompt}\n\n## 用户提示\n${prompt}`, {
      maxTokens: 1000,
      temperature: 0.8
    });

    return NextResponse.json({ content });
  } catch (error) {
    console.error('AI generate error:', error);
    return NextResponse.json({ error: '生成失败' }, { status: 500 });
  }
}
