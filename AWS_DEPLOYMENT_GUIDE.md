# AWS部署指南 - 调情助手

## 方案1：AWS Amplify（推荐）⭐

### 步骤1：准备环境
```bash
# 安装AWS CLI
brew install awscli

# 配置AWS
aws configure
# 输入你的Access Key ID, Secret Access Key, Region (如: us-east-1)
```

### 步骤2：安装Amplify CLI
```bash
npm install -g @aws-amplify/cli
amplify configure
```

### 步骤3：初始化Amplify项目
```bash
# 在项目根目录运行
amplify init
# 选择: React, TypeScript, 使用现有代码
```

### 步骤4：添加API
```bash
amplify add api
# 选择: REST, 创建新Lambda函数, 使用默认配置
```

### 步骤5：部署
```bash
amplify push
```

### 步骤6：发布
```bash
amplify publish
```

---

## 方案2：手动Lambda部署

### 步骤1：创建Lambda函数
1. 登录AWS控制台
2. 进入Lambda服务
3. 创建函数：`ai-flirt-assistant`
4. 运行时：Python 3.9
5. 上传 `lambda_deployment.zip`

### 步骤2：配置环境变量
```
HF_API_KEY=你的HuggingFace_API密钥
```

### 步骤3：创建API Gateway
1. 进入API Gateway服务
2. 创建REST API
3. 创建资源和方法
4. 集成Lambda函数
5. 部署API

### 步骤4：更新前端API URL
修改 `frontend/src/service/sendChatAction.ts` 中的API URL

---

## 环境变量配置

### 必需的API密钥
1. **HuggingFace API Key**
   - 访问: https://huggingface.co/settings/tokens
   - 创建新的Access Token
   - 在AWS Lambda环境变量中设置

### 前端配置
```typescript
// frontend/src/config/api.ts
export const API_BASE_URL = 'https://your-api-gateway-url.amazonaws.com/prod';
```

---

## 成本估算

### AWS Amplify
- 免费额度：每月1000次构建，5GB存储
- 超出后：$0.01/构建，$0.023/GB/月

### AWS Lambda
- 免费额度：每月100万次请求，40万GB-秒
- 超出后：$0.20/100万次请求

### API Gateway
- 免费额度：每月100万次API调用
- 超出后：$3.50/100万次调用

**预计月成本：$0-5（小规模使用）**

---

## 故障排除

### 常见问题
1. **CORS错误**：确保API Gateway配置了CORS
2. **Lambda超时**：增加超时时间到30秒
3. **内存不足**：增加Lambda内存到512MB
4. **API密钥错误**：检查环境变量配置

### 调试命令
```bash
# 查看Lambda日志
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/ai-flirt-assistant

# 测试API
curl -X POST https://your-api-url.amazonaws.com/prod/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "tool": "flirt"}'
```

---

## 下一步
1. 设置自定义域名
2. 配置HTTPS证书
3. 添加监控和告警
4. 设置CI/CD自动部署