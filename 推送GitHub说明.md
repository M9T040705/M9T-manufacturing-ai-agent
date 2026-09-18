# 推送到GitHub步骤

## 第一步：在GitHub上创建仓库

1. 打开 https://github.com/new
2. 仓库名填：`manufacturing-ai-agent`
3. 选 Public（公开）或 Private（私有）
4. 不要勾选 "Add a README file"（我们已经有了）
5. 点 "Create repository"

## 第二步：把代码推上去

创建好仓库后，GitHub会给你一个地址，类似：
`https://github.com/你的用户名/manufacturing-ai-agent.git`

在项目目录下运行：

```bash
cd E:\FDE项目\fde

# 关联远程仓库（把下面的地址换成你自己的）
git remote add origin https://github.com/你的用户名/manufacturing-ai-agent.git

# 推送代码
git branch -M main
git push -u origin main
```

## 第三步：以后改完代码怎么更新

```bash
# 1. 添加所有改动
git add .

# 2. 写一句说明改了什么
git commit -m "改了什么什么"

# 3. 推上去
git push
```

## 注意

- API Key、数据库、备份文件都不会上传（.gitignore已经排除了）
- 别人下载代码后，需要自己装依赖：`pip install -r requirements.txt`
- 配置文件需要自己填：`config/llm.json`
