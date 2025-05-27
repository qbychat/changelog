## [2025-05-26至2025-05-27] 开发报告

### 🚀 新功能开发
- 新增UserEvent消息结构用于实例间通信
  - 涉及文件：`qbychat/rpc/protocol/v1/instance_event.proto`, `qbychat/rpc/protocol/v1/instance_message.proto`
  - 提交记录：407a40c5

### 🔧 代码优化
- 标准化protobuf包命名和文件组织结构
  - 优化类型：架构/可维护性
  - 关键改进：
    - 将模型和服务定义分离到不同proto文件
    - 移除通用common.proto/service.proto文件
    - 优化模块边界以支持自动化依赖管理
  - 涉及文件：多个proto文件（详见提交记录）
  - 提交记录：e8b2d69e

### ⚠️ 重要提醒
- 本次重构涉及protobuf包结构的重大变更，可能影响：
  - 所有依赖proto定义的客户端和服务端代码
  - 需要同步更新相关服务的proto引用路径
- 部署时需要：
  1. 优先更新proto仓库
  2. 重新生成所有gRPC桩代码
  3. 验证各服务间的兼容性