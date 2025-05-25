import os
import requests
from datetime import datetime, timedelta
from dateutil import parser
import re

# Configuration
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

def generate_timestamp():
    """Generate timestamp for file naming"""
    return datetime.now().strftime("%H%M%S")

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
        # 格式化日期范围
        date_range = f"{since_date.strftime('%Y-%m-%d')}至{today.strftime('%Y-%m-%d')}"
        
        prompt = (
            "作为技术文档工程师，请根据以下Git提交记录生成专业开发报告。\n\n"
            "请严格按照以下格式输出报告：\n\n"
            f"## [{date_range}] 开发报告\n\n"
            "### 🚀 新功能开发\n"
            "- 描述新增的功能特性\n"
            "  - 涉及文件：相关文件列表\n"
            "  - 提交记录：SHA简码\n\n"
            "### 🐛 问题修复\n"
            "- 描述修复的问题\n"
            "  - 问题类型：bug/性能/安全等\n"
            "  - 影响范围：描述影响\n"
            "  - 提交记录：SHA简码\n\n"
            "### 🔧 代码优化\n"
            "- 描述代码改进和重构\n"
            "  - 优化类型：性能/可读性/架构等\n"
            "  - 提交记录：SHA简码\n\n"
            "### 📦 依赖更新\n"
            "- 描述依赖库的更新\n"
            "  - 更新内容：版本变化\n"
            "  - 提交记录：SHA简码\n\n"
            "### 📝 文档更新\n"
            "- 描述文档相关的更新\n"
            "  - 更新内容：新增/修改的文档\n"
            "  - 提交记录：SHA简码\n\n"
            "### ⚠️ 重要提醒\n"
            "- 需要特别注意的变更（如破坏性变更）\n"
            "- 部署时需要的特殊操作\n\n"
            "**分析要求：**\n"
            "1. 根据提交信息智能分类到对应章节\n"
            "2. 提取关键技术信息和影响范围\n"
            "3. 如果某个分类没有相关提交，可以省略该章节\n"
            "4. 保持专业和简洁的描述风格\n"
            "5. SHA码只显示前8位\n\n"
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
        
        # Generate filename with timestamp
        timestamp = generate_timestamp()
        filename = f"{run_dir}/{timestamp}_{repo_name.replace('/', '_')}.md"
        
        print(f"准备保存报告，内容长度: {len(content)} 字符")
        print(f"目标路径: {filename}")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Report saved to: {filename}")
        return filename
        
    except Exception as e:
        print(f"保存报告时发生异常: {str(e)}")
        return None

def update_readme(generated_reports):
    """Update README.md with links to generated reports"""
    try:
        readme_path = "README.md"
        
        # Read existing README or create new one
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = "# Daily Development Reports\n\n"
        
        # 获取今天日期的所有报告文件
        date_str = today.strftime('%Y-%m-%d')
        run_dir = f"logs/{date_str}"
        
        all_today_reports = []
        if os.path.exists(run_dir):
            # 遍历今天的目录，获取所有报告文件
            for filename in os.listdir(run_dir):
                if filename.endswith('.md'):
                    file_path = f"{run_dir}/{filename}"
                    all_today_reports.append(file_path)
        
        # 添加本次生成的报告
        for report_path in generated_reports:
            if report_path not in all_today_reports:
                all_today_reports.append(report_path)
        
        # 按文件名中的时间戳排序（降序，新的在前）
        def extract_timestamp(file_path):
            """从文件路径中提取时间戳"""
            filename = os.path.basename(file_path)
            # 文件名格式: HHMMSS_repo_name.md
            timestamp_match = re.match(r'^(\d{6})_', filename)
            if timestamp_match:
                return timestamp_match.group(1)
            return "000000"  # 如果没有匹配到时间戳，给个默认值
        
        all_today_reports.sort(key=extract_timestamp, reverse=True)
        
        # 准备今天的条目
        new_entry = f"\n## {date_str}\n\n"
        for report_path in all_today_reports:
            filename = os.path.basename(report_path)
            # 提取时间戳用于显示
            timestamp = extract_timestamp(report_path)
            formatted_time = f"{timestamp[:2]}:{timestamp[2:4]}:{timestamp[4:6]}"
            
            # 提取仓库名（去掉时间戳前缀和.md后缀）
            repo_name = filename
            if re.match(r'^\d{6}_', filename):
                repo_name = filename[7:]  # 去掉 "HHMMSS_" 前缀
            if repo_name.endswith('.md'):
                repo_name = repo_name[:-3]  # 去掉 ".md" 后缀
            
            new_entry += f"- [{formatted_time}] [{repo_name}]({report_path})\n"
        
        new_entry += "\n"
        
        # 检查今天的日期是否已存在于README中
        date_pattern = f"## {re.escape(date_str)}"
        
        if re.search(date_pattern, content):
            # 替换今天现有的条目
            # 使用更精确的正则表达式来匹配整个日期section
            pattern = f"(## {re.escape(date_str)}.*?)(?=\n## \\d{{4}}-\\d{{2}}-\\d{{2}}|\n# |$)"
            
            # 构建替换内容
            replacement_lines = []
            for path in all_today_reports:
                timestamp = extract_timestamp(path)
                formatted_time = f"{timestamp[:2]}:{timestamp[2:4]}:{timestamp[4:6]}"
                filename = os.path.basename(path)
                
                # 提取仓库名
                repo_name = filename
                timestamp_pattern = r'^\d{6}_'
                if re.match(timestamp_pattern, filename):
                    repo_name = filename[7:]  # 去掉时间戳前缀
                if repo_name.endswith('.md'):
                    repo_name = repo_name[:-3]  # 去掉.md后缀
                
                replacement_lines.append(f"- [{formatted_time}] [{repo_name}]({path})")
            
            replacement = f"## {date_str}\n\n" + "\n".join(replacement_lines) + "\n"
            
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        else:
            # 在README中添加新条目
            # 找到合适的插入位置（按日期降序）
            lines = content.split('\n')
            insert_index = len(lines)
            
            # 寻找插入位置：找到第一个比今天日期小的日期
            for i, line in enumerate(lines):
                date_match = re.match(r'^## (\d{4}-\d{2}-\d{2})', line)
                if date_match:
                    existing_date = date_match.group(1)
                    if existing_date < date_str:
                        insert_index = i
                        break
            
            # 在找到的位置插入新条目
            new_entry_lines = new_entry.strip().split('\n')
            for j, new_line in enumerate(reversed(new_entry_lines)):
                lines.insert(insert_index, new_line)
            
            content = '\n'.join(lines)
        
        # 写入更新后的README
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"README.md updated with {len(all_today_reports)} report links (sorted by time)")
        return True
        
    except Exception as e:
        print(f"更新 README.md 时发生异常: {str(e)}")
        return False

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
    if not github_token:
        missing_vars.append('GITHUB_TOKEN')
    if not api_key:
        missing_vars.append('DEEPSEEK_API_KEY')
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        return
    
    # Process additional repositories
    additional_reports = []
    for repo in additional_repos:
        report_path = process_repository(repo)
        if report_path:
            additional_reports.append(report_path)

    print("\nReport generation complete!")
        
    if additional_reports:
        print("Generated repository reports:")
        for report in additional_reports:
            print(f"- {report}")
        
        # Update README.md with links to generated reports
        print("\nUpdating README.md...")
        if update_readme(additional_reports):
            print("README.md updated successfully!")
        else:
            print("Failed to update README.md")
    else:
        print("No repository reports generated")

if __name__ == "__main__":
    main()
