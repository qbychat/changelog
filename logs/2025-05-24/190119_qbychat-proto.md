## [2025-05-23至2025-05-24] 开发报告

### 🚀 新功能开发
- 新增Conversation相关协议定义
  - 涉及文件：qbychat/websocket/conversation/v1/common.proto, qbychat/websocket/conversation/v1/service.proto
  - 提交记录：154c07cb

- 在RPCRequestMethod中添加Sync方法
  - 涉及文件：qbychat/websocket/protocol/v1/common.proto
  - 提交记录：4f1a55b0

### 🐛 问题修复
- 修复文件引用错误"client_info.proto does not exist"
  - 问题类型：bug
  - 影响范围：session服务相关协议文件
  - 提交记录：00a20440

### 🔧 代码优化
- 统一RPC命名规范使用PascalCase
  - 优化类型：代码规范
  - 提交记录：134d79ba

### 📦 依赖更新
- 添加buf.yaml配置文件并更新相关协议文件
  - 更新内容：新增buf构建配置，调整多个proto文件格式
  - 提交记录：099a1352

### ⚠️ 重要提醒
- 本次更新涉及多个proto文件的格式调整和命名规范变更，建议开发者在合并代码后：
  1. 重新生成所有proto相关代码
  2. 检查所有RPC调用的命名是否符合新的PascalCase规范
  3. 确保构建系统已集成buf工具链