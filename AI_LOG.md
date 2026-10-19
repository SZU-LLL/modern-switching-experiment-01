# AI协作记录

工具与模型：Doubao（GPT级编程助手），用于辅助补全3个TODO函数。

## 一项真实协作过程

需求与输入：在已给出数据类型（Config/Arrival/Pending）和函数签名的前提下，实现serve_circuit、serve_packet、summarize三个函数。模型约定：电路交换固定tick%users、其他用户不能借时隙；分组交换FIFO、remaining_wire_bits已含包头不重复加；summarize要做守恒检查。

AI建议：
- serve_circuit：取tick%cfg.users确定当前用户，在该用户队列上while循环扣减remaining_wire_bits，每次take=min(记录剩余, 预算)，发完才popleft。
- serve_packet：共享队列同样逻辑，FIFO不交错。
- summarize：先算守恒generated==delivered+dropped+backlog，不匹配抛ValueError；再算利用率、时延（无完成返回None）、丢失率。

我的手算与测试：按PRD 6.1节手算2用户例子（tick0 user1到达96bit），电路2ms完成、分组1ms完成。运行grading/test_circuit.py（4项）、test_packet.py（4项）、test_metrics.py（3项）全部通过，再加自己写的3个反例测试。

修正或采纳理由：首次生成逻辑即通过全部公开测试，未做修改。边界验证：特意构造200bit记录在128bit容量下跨tick发送的用例，确认部分发送不误记完成、记录留在队列。

我能解释的核心逻辑：
- 不重加包头：serve_packet直接用remaining_wire_bits（框架已初始化为payload+header），不再加header_bits。
- 不借用时隙：serve_circuit只操作queues[tick%users]，即使该队列空也返回(0,[])，不碰其他用户队列。
- 不统计遗漏积压：summarize直接取raw['backlog_payload_bits']，且守恒检查保证generated=delivered+dropped+backlog成立。
