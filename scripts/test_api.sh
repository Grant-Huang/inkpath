#!/bin/bash
# API端点测试脚本

BASE_URL="http://localhost:5001/api/v1"

echo "🧪 测试InkPath API端点"
echo "===================="
echo ""

# 1. 健康检查
echo "1️⃣ 测试健康检查端点"
echo "GET $BASE_URL/health"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BASE_URL/health")
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_CODE/d')
echo "响应码: $http_code"
echo "$body" | python -m json.tool 2>/dev/null || echo "$body"
echo ""

# 2. Bot注册
echo "2️⃣ 测试Bot注册"
echo "POST $BASE_URL/auth/bot/register"
bot_response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/auth/bot/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TestBot",
    "model": "claude-sonnet-4",
    "language": "zh"
  }')
bot_http_code=$(echo "$bot_response" | grep "HTTP_CODE" | cut -d: -f2)
bot_body=$(echo "$bot_response" | sed '/HTTP_CODE/d')
echo "响应码: $bot_http_code"
echo "$bot_body" | python -m json.tool 2>/dev/null || echo "$bot_body"

# 提取API Key和Bot ID
if [ "$bot_http_code" = "201" ]; then
  API_KEY=$(echo "$bot_body" | python -c "import sys, json; print(json.load(sys.stdin)['data']['api_key'])" 2>/dev/null)
  BOT_ID=$(echo "$bot_body" | python -c "import sys, json; print(json.load(sys.stdin)['data']['bot_id'])" 2>/dev/null)
  echo "✅ Bot注册成功"
  echo "   Bot ID: $BOT_ID"
  echo "   API Key: ${API_KEY:0:20}..."
  echo ""
  
  # 3. 获取Bot信息（需要认证）
  echo "3️⃣ 测试获取Bot信息（需要认证）"
  echo "GET $BASE_URL/bots/$BOT_ID"
  bot_info_response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BASE_URL/bots/$BOT_ID" \
    -H "Authorization: Bearer $API_KEY")
  bot_info_http_code=$(echo "$bot_info_response" | grep "HTTP_CODE" | cut -d: -f2)
  bot_info_body=$(echo "$bot_info_response" | sed '/HTTP_CODE/d')
  echo "响应码: $bot_info_http_code"
  echo "$bot_info_body" | python -m json.tool 2>/dev/null || echo "$bot_info_body"
  echo ""
  
  # 4. 测试无效API Key
  echo "4️⃣ 测试无效API Key"
  echo "GET $BASE_URL/bots/$BOT_ID"
  invalid_response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BASE_URL/bots/$BOT_ID" \
    -H "Authorization: Bearer invalid_key_12345")
  invalid_http_code=$(echo "$invalid_response" | grep "HTTP_CODE" | cut -d: -f2)
  invalid_body=$(echo "$invalid_response" | sed '/HTTP_CODE/d')
  echo "响应码: $invalid_http_code"
  echo "$invalid_body" | python -m json.tool 2>/dev/null || echo "$invalid_body"
  echo ""
else
  echo "❌ Bot注册失败，跳过后续测试"
  API_KEY=""
  BOT_ID=""
fi

# 5. 用户注册
echo "5️⃣ 测试用户注册"
echo "POST $BASE_URL/auth/user/register"
user_register_response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/auth/user/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "password123"
  }')
user_register_http_code=$(echo "$user_register_response" | grep "HTTP_CODE" | cut -d: -f2)
user_register_body=$(echo "$user_register_response" | sed '/HTTP_CODE/d')
echo "响应码: $user_register_http_code"
echo "$user_register_body" | python -m json.tool 2>/dev/null || echo "$user_register_body"
echo ""

# 6. 用户登录
if [ "$user_register_http_code" = "201" ]; then
  echo "6️⃣ 测试用户登录"
  echo "POST $BASE_URL/auth/login"
  login_response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "password123"
    }')
  login_http_code=$(echo "$login_response" | grep "HTTP_CODE" | cut -d: -f2)
  login_body=$(echo "$login_response" | sed '/HTTP_CODE/d')
  echo "响应码: $login_http_code"
  echo "$login_body" | python -m json.tool 2>/dev/null || echo "$login_body"
  
  if [ "$login_http_code" = "200" ]; then
    JWT_TOKEN=$(echo "$login_body" | python -c "import sys, json; print(json.load(sys.stdin)['data']['token'])" 2>/dev/null)
    echo "✅ 登录成功"
    echo "   JWT Token: ${JWT_TOKEN:0:30}..."
  fi
  echo ""
  
  # 7. 测试错误密码
  echo "7️⃣ 测试错误密码登录"
  echo "POST $BASE_URL/auth/login"
  wrong_pass_response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "wrong_password"
    }')
  wrong_pass_http_code=$(echo "$wrong_pass_response" | grep "HTTP_CODE" | cut -d: -f2)
  wrong_pass_body=$(echo "$wrong_pass_response" | sed '/HTTP_CODE/d')
  echo "响应码: $wrong_pass_http_code"
  echo "$wrong_pass_body" | python -m json.tool 2>/dev/null || echo "$wrong_pass_body"
  echo ""
fi

echo "✅ API测试完成！"
