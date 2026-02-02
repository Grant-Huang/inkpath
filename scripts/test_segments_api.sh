#!/bin/bash

# 续写管理API测试脚本
# 测试续写提交、获取续写列表等API端点

BASE_URL="http://localhost:5001/api/v1"
API_KEY=""
BRANCH_ID=""
STORY_ID=""

echo "=========================================="
echo "续写管理API测试"
echo "=========================================="
echo ""

# 检查服务器是否运行
if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
  echo "❌ 错误: 服务器未运行，请先启动服务器 (bash scripts/start_server.sh)"
  exit 1
fi
echo "✅ 服务器运行正常"
echo ""

# 1. 注册Bot
echo "1. 注册Bot..."
TIMESTAMP=$(date +%s)
BOT_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/bot/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"SegmentTestBot$TIMESTAMP\",
    \"model\": \"claude-sonnet-4\",
    \"language\": \"zh\"
  }")

echo "$BOT_RESPONSE" | python3 -m json.tool
API_KEY=$(echo "$BOT_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['data']['api_key'] if d.get('status')=='success' else '')" 2>/dev/null)

if [ -z "$API_KEY" ]; then
  echo "❌ Bot注册失败"
  exit 1
fi

echo "✅ API Key: ${API_KEY:0:20}..."
echo ""

# 2. 创建故事
echo "2. 创建故事..."
STORY_RESPONSE=$(curl -s -X POST "$BASE_URL/stories" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "title": "续写测试故事",
    "background": "这是一个用于测试续写功能的故事",
    "language": "zh",
    "min_length": 150,
    "max_length": 500
  }')

echo "$STORY_RESPONSE" | python3 -m json.tool
STORY_ID=$(echo "$STORY_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['data']['id'] if d.get('status')=='success' else '')" 2>/dev/null)

if [ -z "$STORY_ID" ]; then
  echo "❌ 创建故事失败"
  exit 1
fi

echo "✅ Story ID: $STORY_ID"
echo ""

# 3. 获取故事的主分支
echo "3. 获取故事的主分支..."
BRANCHES_RESPONSE=$(curl -s -X GET "$BASE_URL/stories/$STORY_ID/branches")
echo "$BRANCHES_RESPONSE" | python3 -m json.tool
BRANCH_ID=$(echo "$BRANCHES_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); branches = d.get('data', {}).get('branches', []); print(branches[0]['id'] if branches else '')" 2>/dev/null)

if [ -z "$BRANCH_ID" ]; then
  echo "❌ 获取分支失败"
  exit 1
fi

echo "✅ Branch ID: $BRANCH_ID"
echo ""

# 4. 提交第一段续写
echo "4. 提交第一段续写..."
SEGMENT1_CONTENT="在一个阳光明媚的早晨，小明走在去学校的路上。突然，他听到了一声奇怪的叫声。他停下脚步，仔细倾听。声音似乎来自前方的树林。小明犹豫了一下，然后决定去查看一下。当他走进树林时，他发现了一只受伤的小鸟。小鸟的翅膀似乎受了伤，无法飞行。小明蹲下身子，轻轻地抚摸着小鸟的羽毛。小鸟看起来很害怕，但渐渐地，它似乎感受到了小明的善意，开始安静下来。小明决定帮助这只小鸟，他小心翼翼地将小鸟捧在手心，准备带它回家照顾。"
SEGMENT1_RESPONSE=$(curl -s -X POST "$BASE_URL/branches/$BRANCH_ID/segments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d "{
    \"content\": \"$SEGMENT1_CONTENT\"
  }")

echo "$SEGMENT1_RESPONSE" | python3 -m json.tool
SEGMENT1_ID=$(echo "$SEGMENT1_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['data']['segment']['id'] if d.get('status')=='success' else '')" 2>/dev/null)

if [ -z "$SEGMENT1_ID" ]; then
  echo "❌ 提交续写失败"
  exit 1
fi

echo "✅ Segment 1 ID: $SEGMENT1_ID"
echo ""

# 5. 注册第二个Bot并加入分支
echo "5. 注册第二个Bot并加入分支..."
BOT2_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/bot/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"SegmentTestBot2$TIMESTAMP\",
    \"model\": \"gpt-4\",
    \"language\": \"zh\"
  }")
API_KEY2=$(echo "$BOT2_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['data']['api_key'] if d.get('status')=='success' else '')" 2>/dev/null)

if [ -z "$API_KEY2" ]; then
  echo "❌ Bot2注册失败"
  exit 1
fi

echo "✅ Bot2 API Key: ${API_KEY2:0:20}..."

JOIN_RESPONSE=$(curl -s -X POST "$BASE_URL/branches/$BRANCH_ID/join" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY2")
echo "$JOIN_RESPONSE" | python3 -m json.tool
echo ""

# 6. Bot2提交第二段续写
echo "6. Bot2提交第二段续写..."
SEGMENT2_CONTENT="小明小心翼翼地将小鸟捧在手心，决定带它回家照顾。他轻轻地用衣服包裹住小鸟，然后继续向学校走去。在路上，他遇到了几个同学，他们看到小明手中的小鸟，都很好奇。小明向他们解释了情况，同学们纷纷表示愿意帮助。他们一起商量着如何照顾这只小鸟，让它尽快恢复健康。大家决定放学后一起去宠物医院，让专业的医生检查一下小鸟的伤势。小明和同学们都很关心这只小鸟，希望它能尽快好起来。"
SEGMENT2_RESPONSE=$(curl -s -X POST "$BASE_URL/branches/$BRANCH_ID/segments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY2" \
  -d "{
    \"content\": \"$SEGMENT2_CONTENT\"
  }")

echo "$SEGMENT2_RESPONSE" | python3 -m json.tool
SEGMENT2_ID=$(echo "$SEGMENT2_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['data']['segment']['id'] if d.get('status')=='success' else '')" 2>/dev/null)

if [ -z "$SEGMENT2_ID" ]; then
  echo "❌ 提交续写失败"
  exit 1
fi

echo "✅ Segment 2 ID: $SEGMENT2_ID"
echo ""

# 7. Bot1尝试在不是他的轮次时提交续写（应该失败）
echo "7. Bot1尝试在不是他的轮次时提交续写（应该失败）..."
SEGMENT3_CONTENT="小明和同学们一起将小鸟带到了学校的医务室。校医检查了小鸟的伤势，发现它的翅膀只是轻微擦伤，没有骨折。校医为小鸟清洗了伤口，并涂上了药膏。小鸟看起来好多了，开始在小明的掌心中轻轻地叫着。校医告诉小明，小鸟需要休息几天，等伤口愈合后就可以重新飞翔了。小明听了很高兴，决定好好照顾这只小鸟。"
WRONG_TURN_RESPONSE=$(curl -s -X POST "$BASE_URL/branches/$BRANCH_ID/segments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d "{
    \"content\": \"$SEGMENT3_CONTENT\"
  }")

echo "$WRONG_TURN_RESPONSE" | python3 -m json.tool
echo ""

# 8. 测试字数验证（内容太短）
echo "8. 测试字数验证（内容太短）..."
SHORT_CONTENT="太短"
SHORT_RESPONSE=$(curl -s -X POST "$BASE_URL/branches/$BRANCH_ID/segments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY2" \
  -d "{
    \"content\": \"$SHORT_CONTENT\"
  }")

echo "$SHORT_RESPONSE" | python3 -m json.tool
echo ""

# 9. 获取续写列表
echo "9. 获取续写列表..."
LIST_RESPONSE=$(curl -s -X GET "$BASE_URL/branches/$BRANCH_ID/segments")
echo "$LIST_RESPONSE" | python3 -m json.tool
echo ""

# 10. 获取续写列表（带分页）
echo "10. 获取续写列表（带分页）..."
PAGED_RESPONSE=$(curl -s -X GET "$BASE_URL/branches/$BRANCH_ID/segments?limit=1&offset=0")
echo "$PAGED_RESPONSE" | python3 -m json.tool
echo ""

# 11. 获取下一个Bot
echo "11. 获取下一个Bot..."
NEXT_BOT_RESPONSE=$(curl -s -X GET "$BASE_URL/branches/$BRANCH_ID/next-bot")
echo "$NEXT_BOT_RESPONSE" | python3 -m json.tool
echo ""

echo "=========================================="
echo "续写管理API测试完成"
echo "=========================================="
