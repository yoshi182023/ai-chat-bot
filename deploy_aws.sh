#!/bin/bash

echo "🚀 开始部署到AWS..."

# 检查AWS CLI是否安装
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI未安装，请先安装AWS CLI"
    echo "安装命令: brew install awscli"
    exit 1
fi

# 检查AWS配置
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS未配置，请先运行: aws configure"
    exit 1
fi

echo "✅ AWS CLI已配置"

# 1. 构建前端
echo "📦 构建前端..."
cd frontend
npm install
npm run build
cd ..

# 2. 创建Lambda部署包
echo "📦 创建Lambda部署包..."
mkdir -p lambda_package
pip install -r lambda_requirements.txt -t lambda_package/
cp lambda_handler.py lambda_package/
cd lambda_package
zip -r ../lambda_deployment.zip .
cd ..
rm -rf lambda_package

echo "✅ Lambda部署包已创建: lambda_deployment.zip"

# 3. 部署到Lambda
echo "🚀 部署到AWS Lambda..."
aws lambda create-function \
    --function-name ai-flirt-assistant \
    --runtime python3.9 \
    --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/lambda-execution-role \
    --handler lambda_handler.lambda_handler \
    --zip-file fileb://lambda_deployment.zip \
    --timeout 30 \
    --memory-size 512 \
    --environment Variables="{HF_API_KEY=your_huggingface_api_key_here}" \
    --description "AI调情助手Lambda函数" || echo "函数可能已存在，尝试更新..."

# 更新函数代码
aws lambda update-function-code \
    --function-name ai-flirt-assistant \
    --zip-file fileb://lambda_deployment.zip

# 4. 创建API Gateway
echo "🌐 创建API Gateway..."
aws apigatewayv2 create-api \
    --name ai-flirt-assistant-api \
    --protocol-type HTTP \
    --description "AI调情助手API" || echo "API可能已存在"

# 获取API ID
API_ID=$(aws apigatewayv2 get-apis --query 'Items[?Name==`ai-flirt-assistant-api`].ApiId' --output text)
echo "API ID: $API_ID"

# 创建Lambda集成
aws apigatewayv2 create-integration \
    --api-id $API_ID \
    --integration-type AWS_PROXY \
    --integration-uri arn:aws:lambda:$(aws configure get region):$(aws sts get-caller-identity --query Account --output text):function:ai-flirt-assistant \
    --payload-format-version "2.0" || echo "集成可能已存在"

# 创建路由
aws apigatewayv2 create-route \
    --api-id $API_ID \
    --route-key "ANY /{proxy+}" \
    --target "integrations/$(aws apigatewayv2 get-integrations --api-id $API_ID --query 'Items[0].IntegrationId' --output text)" || echo "路由可能已存在"

# 部署API
aws apigatewayv2 create-deployment \
    --api-id $API_ID \
    --stage-name prod

# 获取API URL
API_URL=$(aws apigatewayv2 get-api --api-id $API_ID --query 'ApiEndpoint' --output text)
echo "🎉 部署完成！"
echo "API URL: $API_URL"
echo "前端需要更新API URL为: $API_URL"

# 清理
rm lambda_deployment.zip

echo "✅ 部署完成！请在前端代码中更新API URL"