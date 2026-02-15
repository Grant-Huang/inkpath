import { NextRequest, NextResponse } from 'next/server';
import { LLMClient } from '@/lib/llm';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, context, style_rules } = body;

    if (!message) {
      return NextResponse.json({ error: '消息不能为空' }, { status: 400 });
    }

    const llm = new LLMClient();
    
    const prompt = `你是一个专业的写作助手，帮助作者创作高质量的故事。

${context ? `## 故事背景\n${context}` : ''}

${style_rules ? `## 风格要求\n${style_rules}` : ''}

## 用户问题
${message}

请用简洁、专业的语气回答。如果用户询问写作建议，给出具体、可操作的建议。`;

    const reply = await llm.generate(prompt, {
      maxTokens: 500,
      temperature: 0.7
    });

    return NextResponse.json({ reply });
  } catch (error) {
    console.error('AI chat error:', error);
    return NextResponse.json({ error: 'AI 服务暂时不可用' }, { status: 500 });
  }
}

export async function GET() {
  return NextResponse.json({ 
    status: 'AI chat endpoint ready',
    methods: ['POST']
  });
}
