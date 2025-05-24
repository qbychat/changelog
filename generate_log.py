import os
import requests
from datetime import datetime, timedelta
from dateutil import parser

# 配置参数
repo = os.getenv('GITHUB_REPOSITORY')
api_key = os.getenv('DEEPSEEK_API_KEY')
github_token = os.getenv('GITHUB_TOKEN')
is_manual = os.getenv('IS_MANUAL_TRIGGER', 'false').lower() == 'true'
days_to_cover = int(os.getenv('DAYS_TO_COVER', '1'))

today = datetime.utcnow().date()
since_date = today - timedelta(days=days_to_cover)

print(f"Generating report for period: {since_date} to {today}")
print(f"Manual trigger: {is_manual}")

# 获取 commits
commits_url = f"https://api.github.com/repos/{repo}/commits"
github_headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github.v3+json"
}
params = {
    "since": since_date.isoformat(),
    "until": today.isoformat()
}

response = requests.get(commits_url, headers=github_headers, params=params)
commits = response.json()

if not isinstance(commits, list):
    print(f"Error fetching commits: {commits}")
    exit(1)

# 收集 commit 信息
commit_messages = []
for commit in commits:
    if isinstance(commit, dict):
        sha = commit['sha']
        author = commit['commit']['author']['name']
        message = commit['commit']['message']
        
        # 获取 commit 的 diff
        diff_url = f"https://api.github.com/repos/{repo}/commits/{sha}"
        diff_response = requests.get(diff_url, headers=github_headers)
        diff_data = diff_response.json()
        files_changed = diff_data.get('files', [])
        
        file_changes = []
        for file in files_changed:
            filename = file['filename']
            additions = file['additions']
            deletions = file['deletions']
            changes = file['changes']
            file_changes.append(f"{filename} (+{additions}/-{deletions})")
        
        commit_messages.append(
            f"Author: {author}\n"
            f"Message: {message}\n"
            f"Files changed: {', '.join(file_changes)}\n"
        )

if not commit_messages:
    if is_manual:
        commit_messages.append("No commits found in the selected period. This is a test report for manual trigger.")
    else:
        print("No commits today. Exiting.")
        exit(0)

# 准备发送给 DeepSeek 的 prompt
commits_text = "\n\n".join(commit_messages)
prompt = (
"作为QbyChat项目的技术文档工程师，请根据以下Git提交记录生成专业开发报告。要求：\n"
"1. 严格按Kotlin后端开发规范分类\n"
"2. 突出WebSocket/聊天相关功能\n"
"3. 标注涉及的技术栈（如Ktor/Exposed/Redis）\n\n"
"## [YYYY-MM-DD至YYYY-MM-DD] QbyChat后端开发报告\n"
"### 核心功能迭代\n"
"- [消息模块] 描述变更（使用✅❌标注BREAKING CHANGE）\n"
"  ∟ 技术细节：涉及的技术组件（如Ktor WebSocket路由）\n"
"  ∟ 相关PR：#123 (@提交者)\n"
"### 服务端修复\n"
"- [稳定性] 描述问题（标注严重级别：SEV1/SEV2）\n"
"  ∟ 根本原因：简明技术分析\n"
"  ∟ 修复方案：如补丁策略/热修复\n"
"### 架构调整\n"
"- [数据库] Exposed表结构变更\n"
"  ∟ 迁移指南：需执行的Flyway脚本\n"
"### 开发者须知\n"
"- 需特别注意的API变更\n"
"- 新引入的依赖库\n\n"
"报告要求：\n"
"1. 使用专业术语（如'消息持久化'而非'存聊天记录'）\n"
"2. 区分功能类型：核心功能/辅助功能/技术债清理\n"
"3. 包含影响评估（性能/安全性/兼容性）\n\n"
"以下是提交记录：\n\n"
f"{commits_text}"
)

print("Generated prompt:", prompt)

# 调用 DeepSeek API
deepseek_url = "https://api.deepseek.com/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
data = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "temperature": 0,
    "stream": False
}

response = requests.post(deepseek_url, headers=headers, json=data)
result = response.json()
report_content = result['choices'][0]['message']['content']

issue_title = f"Development Report - {since_date} to {today}"
issue_url = f"https://api.github.com/repos/{repo}/issues"
issue_data = {
    "title": issue_title,
    "body": report_content,
    "labels": ["development-report"]
}
# 创建 Issue 的代码修改为：
issue_response = requests.post(issue_url, headers=github_headers, json=issue_data)
if issue_response.status_code != 201:
    print(f"Failed to create issue. Status: {issue_response.status_code}, Response: {issue_response.text}")
else:
    print(f"Issue created at: {issue_response.json().get('html_url')}")

print("Report generated and posted as issue.")
