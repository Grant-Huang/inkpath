/**
 * LLM Client
 * 
 * 支持多种 LLM 提供商：
 * - Ollama (本地)
 * - MiniMax
 * - Google Gemini
 */

export interface LLMConfig {
  provider: 'ollama' | 'minimax' | 'gemini';
  model: string;
  baseUrl?: string;
  apiKey?: string;
}

export interface GenerateOptions {
  maxTokens?: number;
  temperature?: number;
  topP?: number;
}

export class LLMClient {
  private config: LLMConfig;
  private provider: string;

  constructor(config?: Partial<LLMConfig>) {
    // 从环境变量读取配置
    this.config = {
      provider: (process.env.LLM_PROVIDER as 'ollama' | 'minimax' | 'gemini') || 'ollama',
      model: process.env.LLM_MODEL || 'qwen3:32b',
      baseUrl: process.env.LLM_BASE_URL || 'http://localhost:11434',
      apiKey: process.env.LLM_API_KEY,
      ...config
    };
    this.provider = this.config.provider;
  }

  /**
   * 生成文本
   */
  async generate(prompt: string, options: GenerateOptions = {}): Promise<string> {
    const { maxTokens = 1000, temperature = 0.7, topP = 0.9 } = options;

    switch (this.provider) {
      case 'ollama':
        return this.generateWithOllama(prompt, { maxTokens, temperature });
      case 'minimax':
        return this.generateWithMiniMax(prompt, { maxTokens, temperature });
      case 'gemini':
        return this.generateWithGemini(prompt, { maxTokens, temperature });
      default:
        throw new Error(`不支持的 LLM 提供商: ${this.provider}`);
    }
  }

  /**
   * Ollama 本地模型
   */
  private async generateWithOllama(prompt: string, options: GenerateOptions): Promise<string> {
    const { maxTokens, temperature } = options;

    const response = await fetch(`${this.config.baseUrl}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: this.config.model,
        prompt,
        stream: false,
        options: {
          num_predict: maxTokens,
          temperature,
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Ollama API 错误: ${response.statusText}`);
    }

    const data = await response.json();
    return data.response;
  }

  /**
   * MiniMax API
   */
  private async generateWithMiniMax(prompt: string, options: GenerateOptions): Promise<string> {
    const { maxTokens, temperature } = options;

    const response = await fetch('https://api.minimax.chat/v1/text/chatcompletion_v2', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.config.apiKey}`
      },
      body: JSON.stringify({
        model: this.config.model,
        messages: [{ role: 'user', content: prompt }],
        max_output_tokens: maxTokens,
        temperature
      })
    });

    if (!response.ok) {
      throw new Error(`MiniMax API 错误: ${response.statusText}`);
    }

    const data = await response.json();
    return data.choices[0].message.content;
  }

  /**
   * Google Gemini API
   */
  private async generateWithGemini(prompt: string, options: GenerateOptions): Promise<string> {
    const { maxTokens, temperature } = options;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };
    if (this.config.apiKey) {
      headers['x-goog-api-key'] = this.config.apiKey;
    }

    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${this.config.model}:generateContent`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: {
            maxOutputTokens: maxTokens,
            temperature
          }
        })
      }
    );

    if (!response.ok) {
      throw new Error(`Gemini API 错误: ${response.statusText}`);
    }

    const data = await response.json();
    return data.candidates[0].content.parts[0].text;
  }

  /**
   * 获取可用模型列表
   */
  async listModels(): Promise<string[]> {
    switch (this.provider) {
      case 'ollama':
        return this.listOllamaModels();
      default:
        return [this.config.model];
    }
  }

  private async listOllamaModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.config.baseUrl}/api/tags`);
      if (!response.ok) return [];
      
      const data = await response.json();
      return data.models?.map((m: any) => m.name) || [];
    } catch {
      return [];
    }
  }
}

// 使用示例
/*
const llm = new LLMClient({
  provider: 'ollama',
  model: 'qwen3:32b',
  baseUrl: 'http://localhost:11434'
});

const content = await llm.generate('请续写这个故事...', {
  maxTokens: 500,
  temperature: 0.7
});
*/
