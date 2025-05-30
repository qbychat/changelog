## [2025-05-29至2025-05-30] 开发报告

### 🚀 新功能开发
- 新增用户资料查询功能
  - 涉及文件：`src/components/main/views/left/DropdownMenu.tsx`, `src/components/main/views/left/LeftPanel.tsx`, `src/components/main/views/left/mvp/CreateChatModal.tsx`, `src/components/main/views/right/IntroView.tsx`, `src/websocket/services/UserService.ts` 等
  - 提交记录：0035566e

### 🐛 问题修复
- 修复CI工作流中的语法错误
  - 问题类型：CI配置
  - 影响范围：依赖图生成工作流
  - 提交记录：ab16b6d8
- 修复Graphviz安装问题
  - 问题类型：CI配置
  - 影响范围：依赖分析工具链
  - 提交记录：cbe023f7
- 修复工作流版本使用问题
  - 问题类型：CI配置
  - 影响范围：GitHub Actions兼容性
  - 提交记录：ea1ab235

### 🔧 代码优化
- 全面重构代码命名规范为kebab-case
  - 优化类型：代码规范/可读性
  - 涉及文件：40+个组件和服务文件
  - 提交记录：305f8123
- 新增依赖分析工作流
  - 优化类型：工程化
  - 提交记录：56827b60

### ⚠️ 重要提醒
- 本次提交包含大规模命名规范变更（kebab-case重构），需注意：
  - 可能影响IDE自动导入功能
  - 需要同步更新相关文档引用
  - 部署前建议全面测试组件交互

**技术重点**：
1. 用户服务新增profile查询能力，涉及WebSocket事件处理改造
2. CI流水线增强依赖可视化分析能力
3. 项目级命名规范统一，提升代码一致性