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

## 第二次协作：参数变化实验与报告补全

工具与模型：DeepSeek Harness（deepseek-flash），用于补做PRD第7节要求的"参数变化证据"，并整理报告中的对应章节。

需求与输入：基线8组结果已存在且不改动；只允许新增附加实验产物，不能改教师框架、公开测试和基线数据。变量为包头大小与缓存配额，其余参数固定。

AI做了什么：
- 新增 `analysis/param_sweep.py`，复用教师的 `make_traffic`/`simulate` 和本人的 `summarize`，扫 header_bits=0/16/32/48/64 与 buffer_payload_bits=1024/2048/4096/8192，输出 `results/extra/parameter_sweep.csv`、`parameter_sweep.json`、`param_sweep.png`（共72行长表）。
- 首次运行报 `SyntaxWarning: invalid escape sequence '\.'`，原因是模块docstring里的Windows路径，改成raw字符串后重新运行，退出码0。
- 在报告中补"参数变化分析"一节，表格数值直接从CSV抄录。
- 补齐报告其余部分：公平比较的固定条件、缓存准入手算（AC07口径）、四场景逐条解读、数据自洽性说明、复现说明（环境/命令/预期结果）。

我的核对：扫描中 header_bits=32、buffer_payload_bits=4096 那几行与基线 `results/comparison.csv` 逐项一致，说明扫描没有改变基线的计量口径；重跑 `pytest grading student_tests`（26项）仍全部通过，`grading/calculate_grade.py` 自动分仍为 70/100；`comparison.csv` 与 `parameter_sweep.csv` 各连跑两次，SHA256 一致（`0A8BCBFF…`、`EBD7BA93…`），报告里的可复现性说法由此而来。

采纳理由：脚本只新增文件、不改 `src/`，基线产物字节不变；报告新增章节的每个数字都能在 `parameter_sweep.csv` 里查到。本段由AI助手代为整理，数据可对照该CSV复核。
