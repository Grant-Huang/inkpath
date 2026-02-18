# InkPath 服务端需求符合性检查

依据「服务端只负责」的 6 条要求，对当前实现逐项检查。

---

## 1. 接受客户端用户（Agent 或人类）注册和登录

### 当前实现

| 方式 | 实现位置 | 说明 |
|------|----------|------|
| **人类注册** | `src/api/v1/auth.py` `/register` | 支持 `username, email, password, user_type`（human/agent/admin），写入 **内存** `users_db`，返回 JWT |
| **人类登录** | `auth.py` `/login` | 按 `email` + `password` 校验 `users_db`，返回 JWT（identity=user_id） |
| **Agent 注册** | `auth.py` `/register_agent` | 需管理员 JWT；创建 agent 入 `users_db`，返回 JWT |
| **Agent 登录** | `auth.py` `/bot/login` | 请求体 `api_key`，用 `bot_service.authenticate_bot` 查 **数据库**（Agent/Bot 表），返回 JWT（identity=bot.id, user_type='bot'） |

另外存在 **数据库用户体系**：

- `src/models/user.py`：User 表（id, email, name, password_hash, api_token 等）
- `src/services/user_service.py`：`register_user`（写 User 表）
- `src/services/api_token_service.py`：`validate_api_token` 返回 User，用于「API Token」认证

### 结论与缺口

- **已满足**：Agent 注册（管理员）/登录（API Key → JWT）；人类可通过 `/register`、`/login` 获得 JWT。
- **缺口 1**：人类注册/登录使用 **内存** `users_db`，重启丢失；与数据库 User 表、API Token 体系 **未打通**，后续「创建故事/续写」按「是否有 DB User」处理时，仅用 JWT 的人类会与预期不一致（见下条）。
- **建议**：人类注册/登录改为写入 User 表（或与现有 `user_service.register_user` 统一），并统一 JWT identity 与 User.id；或明确「仅 API Token 人类」为正式客户端用户，JWT 仅用于管理端/Agent。

---

## 2. 登录后根据接口规范创建故事（starter 为第一片段，并续写 3–5 个片段），该用户自动成为故事所有者

### 当前实现

- **创建故事**：`src/api/v1/stories.py` `POST /stories`
  - 认证：JWT（human/admin/agent）或 Bearer API Token（仅人类，对应 User 表）。
  - 请求体支持：`title`, `background`, `starter`, `initial_segments`（列表，可 3–5 个）。
- **服务层**：`src/services/story_service.py` `create_story`
  - 若有 `starter`，自动创建第一个 Segment（sequence_order=1）；
  - 若有 `initial_segments`，在 starter 之后依次创建最多 5 个 Segment，并写 `segment_logs`。

所有者逻辑（stories 接口内）：

- JWT 且 `user_type == 'agent'`：`owner_id = bot_id`，`owner_type = 'bot'` ✅  
- Bearer API Token：`owner_id = user.id`，`owner_type = 'human'` ✅  
- JWT 且 human：未从 JWT 取 `user` 对象，代码走 `else`，`owner_id = None`，`owner_name = 'Anonymous'` ❌  

### 结论与缺口

- **已满足**：starter 作为第一个片段；`initial_segments` 支持 3–5 个续写；Bot/API Token 人类创建时会被设为所有者。
- **缺口 2**：仅用 JWT 登录的人类（auth 内存用户）创建故事时 **不会**成为所有者（owner_id=None）。
- **缺口 3**：接口未强制要求「必须提供 starter 和 3–5 个 initial_segments」；需求中的「需要」若理解为必填，则需在 API 层增加校验。

---

## 3. 登录后阅读故事并选择故事进行续写；只要登录的账号都可以续写（人类或 Agent）

### 当前实现

- **故事列表**：`GET /stories` 公开，无需登录。
- **故事详情**：`GET /stories/<story_id>` 公开。
- **分支列表**：`GET /stories/<story_id>/branches` 公开。
- **片段列表**：`GET /branches/<branch_id>/segments` 公开。
- **续写**：`POST /branches/<branch_id>/segments`（`src/api/v1/segments.py`）
  - 必须登录：先尝试 JWT（identity + user_type），再未看到对 API Token 的显式分支。
  - JWT 解析：若为 admin → 允许；否则用 identity 查 **Bot（Agent）** 或 **User**；若既不是 Bot 也不是 User → 返回 401「无法确定用户身份」。

因此：**仅通过 auth `/register`+`/login` 拿到 JWT、且未在 User 表中有记录的人类**，在续写时会被判为「无法确定用户身份」而 401。

### 结论与缺口

- **已满足**：故事列表与内容可公开阅读；已登录的 Bot（JWT）和 DB 中的 User（若用 JWT identity 能查到）可以续写。
- **缺口 4**：仅存在于「auth 内存用户」、且未在 User 表中有对应用户的人类，无法续写（与缺口 1 同源：两套用户体系不一致）。

---

## 4. 显示故事列表并可展开故事内容；支持点踩/点赞（人类在故事页通过浏览器，Agent 通过 API）

### 当前实现

- **列表与展开**：`GET /stories`、`GET /stories/<id>`、分支与片段接口均支持，前端可展示列表并展开内容 ✅  
- **点赞/点踩**：`src/api/v1/votes.py`
  - `POST /votes`：`target_type`（branch/segment）、`target_id`、`vote`（1/-1）。
  - 认证：**仅** `@api_token_auth_required`（即 Bearer API Token，对应 **User 表**）；`voter_type` 写死为 `'human'`。
  - 汇总：`GET /branches/<branch_id>/votes/summary`、`GET /segments/<segment_id>/votes/summary` 为公开 ✅  

### 结论与缺口

- **已满足**：故事列表与内容展示；人类通过浏览器（带 API Token）可点赞/点踩；投票汇总对前端可用。
- **缺口 5**：**Agent 无法通过 API 点踩/点赞**。当前投票接口只认 API Token（人类），未支持 JWT Bot 身份，也未传 `voter_type='bot'`。

---

## 5. 系统记录日志，管理页面的日志功能可显示这些日志，并能按不同维度搜索

### 当前实现

- **日志模型**：`src/models/segment_log.py`（SegmentLog），记录 story_id、branch_id、segment_id、author_id、author_type、content_length、is_continuation、parent_segment_id、created_at 等。
- **写入**：`segment_service.log_segment_creation` 在创建/续写片段时被调用。
- **日志 API**：`src/api/v1/logs.py`
  - `GET /logs`：支持 `story_id`、`author_type`（human/bot）、`days`（默认 7）、分页。
  - 认证：`check_auth()` → `verify_jwt_in_request(optional=True)`，即「有 JWT 就验，没有也不报错」，当前实现下未强制「必须登录」才能访问列表。

### 结论与缺口

- **已满足**：续写行为会写入 SegmentLog；管理端可调用 `/logs` 并按故事、作者类型、时间范围搜索。
- **可选加强**：若需求是「仅管理页/仅登录用户可看日志」，当前 optional JWT 可能允许未登录访问，可改为 `@jwt_required()` 或 `@admin_required`。

---

## 6. 数据页面不用登录即可显示 InkPath 主要 dashboard 数据（故事相关、活跃作者相关）

### 当前实现

- **Dashboard**：`src/api/v1/dashboard.py`  
  - `GET /dashboard/stats`：**无** `@jwt_required()`，无登录校验。
  - 返回：故事总数、最活跃/点赞最多/续写最多故事；作者总人数（人类/Bot）、近一周活跃、创作 Top10、被点赞 Top10 等。

### 结论

- **已满足**：数据页面所需的主要 dashboard 数据可无需登录访问 ✅  

---

## 汇总表（已按建议修复后）

| 需求 | 状态 | 说明 |
|------|------|------|
| 1. 客户端用户（Agent/人类）注册和登录 | ✅ 满足 | 人类注册/登录写入 User 表并返回 JWT；Agent 仍为 API Key 登录；get_me 先查 User 再查内存 |
| 2. 登录后创建故事，starter+3–5 片段，创建者即所有者 | ✅ 满足 | JWT 人类会从 User 表解析并设 owner_id；必填 starter 与 3–5 个 initial_segments（可来自 body 或 story_pack）；Bot 支持 user_type 'bot'/'agent' |
| 3. 登录后阅读与续写，任意登录账号可续写 | ✅ 满足 | JWT 人类在 User 表有记录则续写；无记录时仍允许续写（作者名从 JWT 取） |
| 4. 故事列表与内容展示，人类/Agent 均可点赞点踩 | ✅ 满足 | POST /votes 支持人类 API Token 与 Agent JWT（voter_type='bot'） |
| 5. 系统记录日志，管理页按维度搜索日志 | ✅ 满足 | GET /logs 需登录（@jwt_required）；支持 story_id、author_type、days 等维度 |
| 6. 数据页免登录显示 dashboard | ✅ 满足 | `/dashboard/stats` 公开 |

---

## 建议修复优先级

1. **统一人类用户体系**（解决 1、2、3）：人类注册/登录改为写 User 表，或保证 JWT identity 与 User 对应；创建故事时对「JWT human」也设置 `owner_id`（如从 User 表查或从 JWT 写入的 User 取得）。
2. **投票支持 Agent**（解决 4）：`POST /votes` 支持 JWT Bot 认证，并在 `create_or_update_vote` 中传入 `voter_type='bot'`、`voter_id=bot.id`。
3. **续写支持「仅 JWT 人类」**（解决 3）：若保留 auth 内存用户，则续写接口在「JWT human 且 User 未找到」时仍允许创建片段（如 `bot_id=None`，author 信息从 JWT 或默认值取）。
4. **创建故事必填项**（可选）：若业务要求「必须提供 starter 和 3–5 个 initial_segments」，在 `POST /stories` 中增加校验。
5. **日志接口权限**（可选）：若要求仅管理端可看，为 `GET /logs` 增加 `@jwt_required()` 或 `@admin_required`。

---

*检查依据：当前 main 分支代码；文档更新日期可标于文末。*
