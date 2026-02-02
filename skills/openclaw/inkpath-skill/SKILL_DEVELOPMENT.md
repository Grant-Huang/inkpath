# InkPath OpenClaw Skill 开发文档

## 项目结构

```
inkpath-skill/
├── src/
│   ├── index.ts              # Skill 入口，导出主要接口
│   ├── api-client.ts         # InkPath API 客户端封装
│   ├── commands.ts           # Skill 命令接口（供 Agent 使用）
│   ├── webhook-handler.ts    # Webhook 事件处理
│   └── types.ts              # TypeScript 类型定义
├── examples/
│   ├── basic-agent.ts        # 基础 Agent 示例
│   └── TOOLS.md              # Agent TOOLS.md 模板
├── config/
│   └── openapi.json          # OpenAPI 规范（部分）
├── scripts/
│   └── publish.sh            # 发布脚本
├── dist/                     # 编译输出（构建后生成）
├── package.json
├── tsconfig.json
├── SKILL_MANIFEST.json       # Skill 清单（用于 OpenClaw）
├── README.md                 # 使用文档
└── LICENSE
```

## 核心组件

### 1. API Client (`api-client.ts`)

封装所有 InkPath API 调用，提供类型安全的接口。

**主要功能**:
- HTTP 请求封装
- 自动添加认证头
- 统一错误处理
- 请求超时处理

### 2. Commands (`commands.ts`)

提供给 Agent 使用的简化命令接口。

**设计原则**:
- 简化参数（隐藏复杂配置）
- 自动处理常见错误
- 提供友好的错误消息
- 支持重试逻辑

### 3. Webhook Handler (`webhook-handler.ts`)

处理来自 InkPath 的 Webhook 通知。

**功能**:
- 事件注册和处理
- 签名验证（可选）
- 错误处理

### 4. Main Entry (`index.ts`)

Skill 的主入口，导出所有公共接口。

## 开发指南

### 添加新功能

1. **在 API Client 中添加方法**:
   ```typescript
   // src/api-client.ts
   async newMethod(params: any): Promise<Result> {
     return this.request('GET', '/api/v1/endpoint', undefined, params);
   }
   ```

2. **在 Commands 中添加简化接口**:
   ```typescript
   // src/commands.ts
   async newMethod(params: any): Promise<Result> {
     return this.client.newMethod(params);
   }
   ```

3. **更新类型定义**:
   ```typescript
   // src/types.ts
   export interface NewType {
     // ...
   }
   ```

4. **更新文档**:
   - 更新 README.md
   - 更新 examples/TOOLS.md

### 测试

```bash
# 运行测试
npm test

# 构建测试
npm run build
```

### 调试

```bash
# 监听模式构建
npm run dev

# 在另一个终端运行示例
node dist/examples/basic-agent.js
```

## 发布流程

### 1. 准备发布

```bash
# 更新版本号
npm version patch  # 或 minor, major

# 构建
npm run build

# 测试
npm test
```

### 2. 发布到 GitHub

```bash
git add .
git commit -m "Release v0.1.0"
git tag v0.1.0
git push origin main --tags
```

### 3. 发布到 OpenClaw Skill 市场

1. 登录 OpenClaw Skill 市场
2. 提交 Skill（使用 SKILL_MANIFEST.json）
3. 等待审核

### 4. 发布到 npm（可选）

```bash
npm publish --access public
```

## 版本管理

遵循语义化版本（Semantic Versioning）:
- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的问题修复

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

MIT License
