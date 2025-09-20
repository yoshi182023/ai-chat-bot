#!/bin/bash

echo "🚀 开始部署到AWS Amplify..."

# 检查依赖
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI未安装"
    echo "请运行: brew install awscli && aws configure"
    exit 1
fi

if ! command -v amplify &> /dev/null; then
    echo "❌ Amplify CLI未安装"
    echo "请运行: npm install -g @aws-amplify/cli"
    exit 1
fi

echo "✅ 依赖检查通过"

# 构建前端
echo "📦 构建前端..."
cd frontend
npm install
npm run build
cd ..

echo "✅ 前端构建完成"

# 检查是否已初始化Amplify
if [ ! -d "amplify" ]; then
    echo "🔧 初始化Amplify项目..."
    amplify init
fi

# 检查是否已添加API
if ! amplify status | grep -q "api"; then
    echo "🔧 添加API..."
    amplify add api
fi

# 检查是否已添加hosting
if ! amplify status | grep -q "hosting"; then
    echo "🔧 添加hosting..."
    amplify add hosting
fi

# 部署
echo "🚀 部署到AWS..."
amplify push --yes

# 发布
echo "🌐 发布应用..."
amplify publish --yes

echo "🎉 部署完成！"
echo "你的应用URL将在上面显示"
echo "记得在AWS控制台设置环境变量 HF_API_KEY"