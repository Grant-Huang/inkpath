# 墨径 (InkPath) - 故事包模板说明

## 一、什么是故事包？

故事包是一组Markdown文件，用于定义故事的基础设定、证据、立场、角色等。这些文件会被AI续写者读取，作为续写的规则和约束。

---

## 二、文件清单

### 必填文件

1. **`00_meta.md`** - 故事元信息
   - 故事的基本信息（标题、时代、类型等）
   - 系统用于索引和路由

2. **`10_evidence_pack.md`** - 证据包 ⭐ **最重要**
   - 提供"第1层残篇"，决定历史感
   - 每条证据必须有缺口和可争论点
   - **强烈建议提供**，否则AI容易写成"全知视角"

3. **`20_stance_pack.md`** - 立场包 ⭐ **最重要**
   - 提供"第2层立场"，决定冲突
   - 每个立场必须有利益、恐惧、代价
   - **强烈建议提供**，否则AI容易写成"单一观点"

### 建议文件

4. **`30_cast.md`** - 角色卡
   - 提供"第3层个体"，决定拼图
   - 每个角色必须有认知盲区

5. **`40_plot_outline.md`** - 剧情大纲
   - 信息流大纲（不是三幕结构）

6. **`50_constraints.md`** - 约束与边界
   - 硬约束、软约束、内容边界

7. **`60_sources.md`** - 来源清单
   - 可追溯性

### 可选文件

8. **`31_locations.md`** - 地点卡
   - 地点的物理和信息传播约束

9. **`32_objects_terms.md`** - 物件/术语卡
   - 用于一致性检查

---

## 三、如何使用模板

### 步骤1：下载模板包

从平台下载完整的故事包模板：
```
story-pack-template/
├── 00_meta_template.md
├── 10_evidence_pack_template.md
├── 20_stance_pack_template.md
├── 30_cast_template.md
├── 40_plot_outline_template.md
├── 50_constraints_template.md
├── 60_sources_template.md
├── 31_locations_template.md
└── 32_objects_terms_template.md
```

### 步骤2：复制并重命名

将模板文件复制并重命名（去掉`_template`后缀）：
```
my-story/
├── 00_meta.md
├── 10_evidence_pack.md
├── 20_stance_pack.md
├── 30_cast.md
├── 40_plot_outline.md
├── 50_constraints.md
└── 60_sources.md
```

### 步骤3：填写内容

按照模板中的指南填写内容。

### 步骤4：上传到平台

在创建故事时，上传所有MD文件。

---

## 四、参考示例

查看 `demo/` 目录下的示例文件：
- `demo/00_meta.md`
- `demo/10_evidence_pack.md`
- `demo/20_stance_pack.md`
- `demo/30_cast.md`
- `demo/40_plot_outline.md`
- `demo/50_constraints.md`
- `demo/60_sources.md`

---

## 五、帮助文档

- **人类版帮助文档**：`docs/10_故事发起者帮助文档_人类版.md`
- **AI版帮助文档**：`docs/11_故事发起者帮助文档_AI版.md`
- **AI续写规则**：`docs/12_AI续写规则文档.md`

---

## 六、核心原则

记住这句话：

> **你不是在写"设定集"，你是在准备"考古现场"。**  
> 让AI和读者去挖掘、争论、拼图，而不是直接告诉他们答案。

**关键文件**：
- 证据包决定历史感
- 立场包决定冲突
- 角色卡决定拼图
