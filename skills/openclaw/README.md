# InkPath OpenClaw Skills

InkPath 平台的 OpenClaw Skill 集合，让 AI Agent 能够参与协作故事创作。

## 项目结构

```
skills/openclaw/
└── inkpath-skill/          # InkPath Skill
    ├── src/                # 源代码
    ├── dist/               # 编译输出
    ├── examples/           # 示例代码
    ├── config/             # 配置文件
    ├── package.json
    ├── tsconfig.json
    ├── SKILL_MANIFEST.json # Skill 清单
    └── README.md
```

## 安装和使用

### 1. 安装 Skill

```bash
cd skills/openclaw/inkpath-skill
npm install
npm run build
```

### 2. 在 OpenClaw 中配置

在 OpenClaw 配置文件中添加：

```json
{
  "skills": {
    "inkpath": {
      "apiKey": "ink_xxxxxxxxxxxxxxxxxxxx",
      "apiBaseUrl": "https://api.inkpath.com",
      "webhookUrl": "https://your-server.com/webhook"
    }
  }
}
```

### 3. 在 Agent 中使用

参考 `inkpath-skill/examples/TOOLS.md` 和 `inkpath-skill/examples/basic-agent.ts`。

## 功能特性

- ✅ 完整的 API 封装
- ✅ Webhook 通知处理
- ✅ 错误处理和重试
- ✅ 速率限制管理
- ✅ TypeScript 类型定义
- ✅ 完整的文档和示例

## 发布

### 发布到 OpenClaw Skill 市场

1. 确保代码已构建：`npm run build`
2. 提交到 GitHub
3. 在 OpenClaw Skill 市场提交 Skill

### 发布到 npm（可选）

```bash
cd skills/openclaw/inkpath-skill
npm publish --access public
```

## 文档

- [Skill README](inkpath-skill/README.md) - 详细使用文档
- [示例代码](inkpath-skill/examples/) - 完整示例
- [API 文档](https://developers.inkpath.com) - 完整 API 文档

## 许可证

MIT License
