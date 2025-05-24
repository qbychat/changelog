import os
import requests
import hashlib
from datetime import datetime, timedelta
from dateutil import parser

# Configuration
current_repo = os.getenv('GITHUB_REPOSITORY')
api_key = os.getenv('DEEPSEEK_API_KEY')
github_token = os.getenv('GITHUB_TOKEN')
is_manual = os.getenv('IS_MANUAL_TRIGGER', 'false').lower() == 'true'
days_to_cover = int(os.getenv('DAYS_TO_COVER', '1'))
additional_repos_str = os.getenv('ADDITIONAL_REPOS', '')
additional_repos = [repo.strip() for repo in additional_repos_str.split(',') if repo.strip()]

# Date setup
today = datetime.utcnow().date()
since_date = today - timedelta(days=days_to_cover)

print(f"Generating reports for period: {since_date} to {today}")
print(f"Manual trigger: {is_manual}")
print(f"Additional repositories to process: {additional_repos}")

# GitHub API headers
github_headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github.v3+json"
}

def generate_file_hash(content):
    """Generate a short hash for file naming"""
    return hashlib.md5(content.encode()).hexdigest()[:8]

def get_commits(repo, since, until):
    """Fetch commits for a given repository"""
    try:
        commits_url = f"https://api.github.com/repos/{repo}/commits"
        params = {
            "since": since.isoformat(),
            "until": until.isoformat()
        }
        
        print(f"Fetching commits from: {commits_url}")
        response = requests.get(commits_url, headers=github_headers, params=params)
        print(f"GitHub API response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return None
        
        commits = response.json()
        
        if not isinstance(commits, list):
            print(f"Error fetching commits for {repo}: {commits}")
            return None
        
        print(f"Found {len(commits)} commits for {repo}")
        return commits
        
    except Exception as e:
        print(f"Exception when fetching commits for {repo}: {str(e)}")
        return None

def process_commits(commits, repo):
    """Process commits and generate commit messages"""
    if not commits:
        return []
    
    commit_messages = []
    
    for commit in commits:
        try:
            if isinstance(commit, dict):
                sha = commit['sha']
                author = commit['commit']['author']['name']
                message = commit['commit']['message']
                
                print(f"Processing commit: {sha[:8]}...")
                
                # Get commit diff
                diff_url = f"https://api.github.com/repos/{repo}/commits/{sha}"
                diff_response = requests.get(diff_url, headers=github_headers)
                
                if diff_response.status_code == 200:
                    diff_data = diff_response.json()
                    files_changed = diff_data.get('files', [])
                    
                    file_changes = []
                    for file in files_changed:
                        filename = file['filename']
                        additions = file['additions']
                        deletions = file['deletions']
                        file_changes.append(f"{filename} (+{additions}/-{deletions})")
                    
                    commit_messages.append(
                        f"Repository: {repo}\n"
                        f"SHA: {sha}\n"
                        f"Author: {author}\n"
                        f"Message: {message}\n"
                        f"Files changed: {', '.join(file_changes) if file_changes else 'No files info'}\n"
                    )
                else:
                    print(f"Failed to get diff for commit {sha}: {diff_response.status_code}")
                    # 即使获取diff失败，也保存基本commit信息
                    commit_messages.append(
                        f"Repository: {repo}\n"
                        f"SHA: {sha}\n"
                        f"Author: {author}\n"
                        f"Message: {message}\n"
                        f"Files changed: Unable to fetch diff\n"
                    )
                    
        except Exception as e:
            print(f"Error processing commit: {str(e)}")
            continue
    
    print(f"Processed {len(commit_messages)} commit messages")
    return commit_messages

def generate_report(commits_text, repo):
    """Generate report using DeepSeek API"""
    try:
        prompt = (
            "作为技术文档工程师，请根据以下Git提交记录生成专业开发报告。要求：\n"
            "1. 严格按开发规范分类\n"
            "2. 突出核心功能变更\n"
            "3. 标注涉及的技术栈\n\n"
            "## [YYYY-MM-DD至YYYY-MM-DD] 开发报告\n"
            "### 核心功能迭代\n"
            "- [模块] 描述变更（使用✅❌标注BREAKING CHANGE）\n"
            "  ∟ 技术细节：涉及的技术组件\n"
            "  ∟ 相关提交：提交哈希\n"
            "### 服务端修复\n"
            "- [稳定性] 描述问题（标注严重级别）\n"
            "  ∟ 根本原因：简明技术分析\n"
            "  ∟ 修复方案\n"
            "### 架构调整\n"
            "- [数据库] 结构变更\n"
            "  ∟ 迁移指南\n"
            "### 开发者须知\n"
            "- 需特别注意的变更\n"
            "- 新引入的依赖库\n\n"
            "报告要求：\n"
            "1. 使用专业术语\n"
            "2. 区分功能类型\n"
            "3. 包含影响评估\n\n"
            "以下是提交记录：\n\n"
            f"{commits_text}"
        )

        # Call DeepSeek API
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

        print(f"准备调用 DeepSeek API，内容长度: {len(prompt)} 字符")
        response = requests.post(deepseek_url, headers=headers, json=data)
        print(f"DeepSeek API 响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"DeepSeek API 错误响应: {response.text}")
            return f"API调用失败，生成基础报告:\n\n{commits_text}"
        
        result = response.json()
        
        if 'choices' not in result or not result['choices']:
            print(f"DeepSeek API 响应格式异常: {result}")
            return f"API响应格式异常，生成基础报告:\n\n{commits_text}"
        
        return result['choices'][0]['message']['content']
        
    except Exception as e:
        print(f"生成报告时发生异常: {str(e)}")
        return f"报告生成异常，生成基础报告:\n\n{commits_text}"

def save_report(content, repo_name):
    """Save report to a markdown file"""
    try:
        # Create logs directory if not exists
        os.makedirs('logs', exist_ok=True)
        
        # Create subdirectory for this run
        run_dir = f"logs/{today.isoformat()}"
        os.makedirs(run_dir, exist_ok=True)
        
        # Generate filename with hash
        file_hash = generate_file_hash(content)
        filename = f"{run_dir}/{repo_name.replace('/', '_')}_report_{file_hash}.md"
        
        print(f"准备保存报告，内容长度: {len(content)} 字符")
        print(f"目标路径: {filename}")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Report saved to: {filename}")
        return filename
        
    except Exception as e:
        print(f"保存报告时发生异常: {str(e)}")
        return None

def process_repository(repo):
    """Process a single repository"""
    print(f"\nProcessing repository: {repo}")
    
    # 检查必要的环境变量
    if not github_token:
        print(f"GitHub token not found, skipping {repo}")
        return None
    
    if not api_key:
        print(f"DeepSeek API key not found, skipping {repo}")
        return None
    
    commits = get_commits(repo, since_date, today)
    
    if not commits:
        if is_manual:
            print(f"No commits found for {repo}, generating test report for manual trigger")
            commits_text = f"No commits found in the selected period ({since_date} to {today}). This is a test report for manual trigger."
        else:
            print(f"No commits found for {repo} in the selected period.")
            return None
    else:
        commit_messages = process_commits(commits, repo)
        if not commit_messages:
            print(f"No valid commit messages processed for {repo}")
            return None
        commits_text = "\n\n".join(commit_messages)
    
    print(f"Generating report for {repo}...")
    report_content = generate_report(commits_text, repo)
    
    # Save report to file
    repo_name = repo.split('/')[-1]
    return save_report(report_content, repo_name)

# 主执行逻辑
def main():
    print("Starting report generation...")
    
    # 检查环境变量
    missing_vars = []
    if not current_repo:
        missing_vars.append('GITHUB_REPOSITORY')
    if not github_token:
        missing_vars.append('GITHUB_TOKEN')
    if not api_key:
        missing_vars.append('DEEPSEEK_API_KEY')
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        return
    
    # Process current repository
    current_repo_report = process_repository(current_repo)

    # Process additional repositories
    additional_reports = []
    for repo in additional_repos:
        if repo and repo != current_repo:
            report_path = process_repository(repo)
            if report_path:
                additional_reports.append(report_path)

    print("\nReport generation complete!")
    if current_repo_report:
        print(f"Current repository report: {current_repo_report}")
    else:
        print("No report generated for current repository")
        
    if additional_reports:
        print("Additional repository reports:")
        for report in additional_reports:
            print(f"- {report}")
    else:
        print("No additional repository reports generated")

if __name__ == "__main__":
    main()
