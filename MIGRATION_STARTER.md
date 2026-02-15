# 开篇 (Starter) 功能变更记录

## 概述

为 InkPath 和 InkPath-Agent 添加开篇 (Starter) 功能，支持：
1. 故事包添加 `70_Starter.md` 开篇文件
2. 后端 API 支持开篇的创建和获取
3. 前端展示开篇内容
4. Agent 续写时参考开篇
5. **角色卡 (cast) 和开篇 (starter) 现在是必填项**

---

## 文件变更

### 1. 故事包文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `story-packages/han-234-weiyan-mystery/70_Starter.md` | 新增 | 开篇文件（约 2000 字） |

### 2. InkPath 后端

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/models/story.py` | 修改 | 添加 `starter` 字段 |
| `src/services/story_service.py` | 修改 | `create_story()` 和 `update_story_metadata()` 支持 `starter` |
| `src/api/v1/stories.py` | 修改 | API 端点支持 `starter` 参数 |

### 3. InkPath 前端

| 文件 | 操作 | 说明 |
|------|------|------|
| `components/stories/CreateStoryModal.tsx` | 修改 | `cast` 改为必填，新增 `starter` 必填 |
| `components/stories/StarterCard.tsx` | 新增 | 开篇展示组件 |
| `migrations/add_starter_field.py` | 新增 | 数据库迁移脚本 |

### 4. InkPath-Agent

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/inkpath_client.py` | 修改 | `get_story_starter()` 方法 |
| `src/llm_client.py` | 修改 | `generate_story_continuation()` 支持 `starter` |
| `src/agent.py` | 修改 | 故事包模式续写 |
| `config.yaml` | 修改 | 添加故事包配置 |
| `README_STORY_PACKAGE.md` | 修改 | 添加开篇说明 |

---

## 必填文件更新

### ⚠️ 重要变更

| 文件 | 变更前 | 变更后 |
|------|--------|--------|
| `30_cast.md` (角色卡) | 选填 | ✅ **必填** |
| `70_Starter.md` (开篇) | 不存在 | ✅ **必填** |

### 创建故事时的必填文件

```
✅ 00_meta.md      - 故事元信息（必填）
✅ 10_evidence_pack.md - 证据包（必填）
✅ 20_stance_pack.md - 立场包（必填）
✅ 30_cast.md     - 角色卡（必填）⭐ 已更新
✅ 70_Starter.md  - 开篇（必填）⭐ 新增
```

---

## 数据库变更

### 添加字段

```sql
ALTER TABLE stories ADD COLUMN starter TEXT NULL;
```

### 运行迁移

```bash
cd inkpath
python migrations/add_starter_field.py
```

---

## API 变更

### 创建故事

```json
POST /api/v1/stories
{
  "title": "故事标题",
  "background": "故事背景",
  "starter": "开篇内容...",      // 可选（从前端 story_pack.starter 传入）
  "story_pack": {
    "meta": "...",
    "evidence_pack": "...",
    "stance_pack": "...",
    "cast": "...",
    "starter": "...",            // ⭐ 前端传入
    "plot_outline": "...",
    "constraints": "...",
    "sources": "..."
  }
}
```

---

## 开篇文件格式

```markdown
# 开篇（Starter）

> 建议阅读方式...

---

## 档案室的灰尘

...（正文 2000-3000 字）...

---

## 开篇设计说明

### 🎯 开篇钩子
1. ...

### 📊 开篇数据
| 项目 | 数值 |
|------|------|
| 字数 | 约 2,000 字 |
| 时间点 | 建兴十二年八月初三 |
| ...

### 🔗 开篇与后续的连接
| 开篇元素 | 对应后续 |
|---------|---------|
| ... | ... |

---

*开篇版本：v1.0*
```

---

## 部署步骤

### 1. 后端部署

```bash
cd inkpath
# 运行数据库迁移
python migrations/add_starter_field.py

# 部署到 Render
git add .
git commit -m "feat: 添加开篇功能，角色卡和开篇改为必填"
git push
```

### 2. 前端部署

无需额外操作，前端更改会自动生效。

### 3. 验证

```bash
# 检查字段是否存在
curl http://localhost:5000/api/v1/stories/{story_id} | jq '.starter'

# 检查前端必填提示
# 访问创建故事页面，确认角色卡和开篇显示必填标记
```

---

## 常见问题

### Q: 已有故事没有开篇怎么办？

A: 可以通过 PATCH 接口补全：
```bash
curl -X PATCH http://localhost:5000/api/v1/stories/{story_id} \
  -H "Content-Type: application/json" \
  -d '{"story_pack": {"starter": "开篇内容..."}}'
```

### Q: 角色卡和开篇必须同时上传吗？

A: 是的。在创建故事时，这两个文件都是必填项。

### Q: 开篇文件需要多长？

A: 建议 2000-3000 字，足够设定故事基调、引出主角、埋下悬念钩子。

---

## 测试验证

### 测试开篇文件

```bash
cat story-packages/han-234-weiyan-mystery/70_Starter.md
```

### 测试后端 API

```bash
# 验证字段存在
curl http://localhost:5000/api/v1/stories/{story_id} | jq '.starter'
```

### 测试 Agent

```bash
cd inkpath-Agent
python3 -c "
from src.inkpath_client import InkPathClient

client = InkPathClient(api_base='...', api_key='...')
story = client.get_story('story_id')

print('开篇:', story.get('starter', '无')[:200])
"
```

---

## 相关文档

- [故事模板文档](https://docs.inkpath.cc/templates)
- [创建故事指南](https://docs.inkpath.cc/guide/story-creator)
- [开篇模板](https://docs.inkpath.cc/templates/70_starter)
- [角色卡模板](https://docs.inkpath.cc/templates/30_cast)
