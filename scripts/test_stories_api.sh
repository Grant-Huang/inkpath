#!/bin/bash
# 故事管理API测试脚本

BASE_URL="http://localhost:5001/api/v1"

echo "📚 测试故事管理API端点"
echo "===================="
echo ""

# 1. 注册Bot（用于创建故事）
echo "1️⃣ 注册测试Bot"
BOT_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/bot/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "StoryTestBot'$(date +%s)'",
    "model": "claude-sonnet-4",
    "language": "zh"
  }')

BOT_ID=$(echo "$BOT_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['data']['bot_id'])" 2>/dev/null)
API_KEY=$(echo "$BOT_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['data']['api_key'])" 2>/dev/null)

if [ -z "$API_KEY" ]; then
  echo "❌ Bot注册失败"
  echo "$BOT_RESPONSE" | python -m json.tool 2>/dev/null || echo "$BOT_RESPONSE"
  exit 1
fi

echo "✅ Bot注册成功"
echo "   Bot ID: $BOT_ID"
echo "   API Key: ${API_KEY:0:20}..."
echo ""

# 2. 创建故事
echo "2️⃣ 创建故事"
STORY_RESPONSE=$(curl -s -X POST "$BASE_URL/stories" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试故事：AI协作创作",
    "background": "这是一个关于AI协作创作故事的测试故事。故事背景设定在一个未来世界，多个AI Agent需要协作完成一个复杂的故事创作任务。",
    "style_rules": "使用第三人称叙述，保持悬疑氛围，每段150-500字",
    "language": "zh",
    "min_length": 150,
    "max_length": 500,
    "story_pack": {
      "meta": "故事类型：科幻悬疑\n时间：未来世界",
      "evidence_pack": "关键证据1：AI系统日志\n关键证据2：创作记录",
      "cast": "主角：AI Agent Alpha\n配角：AI Agent Beta"
    }
  }')

STORY_ID=$(echo "$STORY_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)

if [ -z "$STORY_ID" ]; then
  echo "❌ 创建故事失败"
  echo "$STORY_RESPONSE" | python -m json.tool 2>/dev/null || echo "$STORY_RESPONSE"
  exit 1
fi

echo "✅ 故事创建成功"
echo "   故事ID: $STORY_ID"
echo "$STORY_RESPONSE" | python -m json.tool 2>/dev/null | head -20
echo ""

# 3. 获取故事列表
echo "3️⃣ 获取故事列表"
LIST_RESPONSE=$(curl -s "$BASE_URL/stories?limit=5")
echo "$LIST_RESPONSE" | python -m json.tool 2>/dev/null | head -30
echo ""

# 4. 获取故事详情
echo "4️⃣ 获取故事详情"
DETAIL_RESPONSE=$(curl -s "$BASE_URL/stories/$STORY_ID")
echo "$DETAIL_RESPONSE" | python -m json.tool 2>/dev/null
echo ""

# 5. 更新故事规范
echo "5️⃣ 更新故事规范"
UPDATE_RESPONSE=$(curl -s -X PATCH "$BASE_URL/stories/$STORY_ID/style-rules" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "style_rules": "更新后的规范：使用第一人称，增加对话，保持紧张感"
  }')
echo "$UPDATE_RESPONSE" | python -m json.tool 2>/dev/null
echo ""

# 6. 注册用户（用于创建置顶帖）
echo "6️⃣ 注册测试用户"
USER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/user/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "pinnedtest'$(date +%s)'@example.com",
    "name": "置顶帖测试用户",
    "password": "password123"
  }')

USER_ID=$(echo "$USER_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['data']['user_id'])" 2>/dev/null)

if [ -z "$USER_ID" ]; then
  echo "❌ 用户注册失败"
  echo "$USER_RESPONSE" | python -m json.tool 2>/dev/null || echo "$USER_RESPONSE"
else
  echo "✅ 用户注册成功"
  echo "   用户ID: $USER_ID"
  
  # 7. 用户登录获取JWT
  echo ""
  echo "7️⃣ 用户登录"
  LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"pinnedtest$(date +%s)@example.com\",
      \"password\": \"password123\"
    }")
  
  JWT_TOKEN=$(echo "$LOGIN_RESPONSE" | python -c "import sys, json; d=json.load(sys.stdin); print(d['data']['token'] if d.get('status')=='success' else '')" 2>/dev/null)
  
  if [ -n "$JWT_TOKEN" ]; then
    echo "✅ 登录成功"
    echo "   JWT Token: ${JWT_TOKEN:0:30}..."
    
    # 8. 创建置顶帖
    echo ""
    echo "8️⃣ 创建置顶帖"
    PIN_RESPONSE=$(curl -s -X POST "$BASE_URL/stories/$STORY_ID/pins" \
      -H "Authorization: Bearer $JWT_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "title": "重要提示",
        "content": "这是故事的置顶帖内容，用于说明重要的创作规范和注意事项。",
        "order_index": 0
      }')
    echo "$PIN_RESPONSE" | python -m json.tool 2>/dev/null
    echo ""
    
    # 9. 获取置顶帖列表
    echo "9️⃣ 获取置顶帖列表"
    PINS_LIST_RESPONSE=$(curl -s "$BASE_URL/stories/$STORY_ID/pins")
    echo "$PINS_LIST_RESPONSE" | python -m json.tool 2>/dev/null
  else
    echo "⚠️ 登录失败，跳过置顶帖测试"
  fi
fi

echo ""
echo "✅ 故事管理API测试完成！"
