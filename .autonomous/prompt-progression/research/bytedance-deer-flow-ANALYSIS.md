# GitHub Issues Analysis: DeerFlow

**Repository:** bytedance/deer-flow
**Generated:** 2026-01-19 08:28:43
**Focus Area:** deerflow

## Summary

- **Total issues fetched:** 20
- **New issues analyzed:** 10
- **Previously seen:** 10

## Issue #635: Commit 2510cc6 is broken

**State:** OPEN
**Created:** 2025-10-20T16:30:34Z
**URL:** https://github.com/bytedance/deer-flow/issues/635

### Description

https://github.com/bytedance/deer-flow/commit/2510cc61de76a68d0d98d4b4f5b4490b77fc6a0c 
is broken. it makes all agents don't work, and ouput xml .
all versions before work.

### Analysis

This issue relates to deerflow. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #605: 请问有增加新开会话和查看历史会话的功能的计划吗

**State:** OPEN
**Created:** 2025-09-29T14:26:04Z
**URL:** https://github.com/bytedance/deer-flow/issues/605

### Description



### Analysis

This issue relates to deerflow. Impact assessment needed based on labels and community engagement.

## Issue #603: 请求响应400

**State:** OPEN
**Created:** 2025-09-28T05:54:07Z
**URL:** https://github.com/bytedance/deer-flow/issues/603

### Description

如图，响应及docker日志中显示：Invalid HTTP request received.

<img width="1746" height="611" alt="Image" src="https://github.com/user-attachments/assets/82ee5397-d9f5-4ca6-8bf4-8649ab1186f4" />


Console报错提示
<img width="1946" height="838" alt="Image" src="https://github.com/user-attachments/assets/c81b315c-2d19...

### Analysis

This issue relates to deerflow. Related to **installation** or **setup**. Impact assessment needed based on labels and community engagement.

## Issue #584: reporter 节点后添加一个节点未运行如何排查？

**State:** OPEN
**Created:** 2025-09-15T16:19:07Z
**URL:** https://github.com/bytedance/deer-flow/issues/584

### Description

在nodes.py文件中新建了一个节点。

```
def html_reporter_node(state: State, config: RunnableConfig):
    """HTML Reporter node that write a html report."""
    logger.info(">>>> HTML Reporter write html report")
    configurable = Configuration.from_runnable_config(config)
...
```



并在builder.py中创建了reporter到htm...

### Analysis

This issue relates to deerflow. Related to **installation** or **setup**. Impact assessment needed based on labels and community engagement.

## Issue #579: 输出是event_data 应该是AIMessagechunk 类型的  但是我的  event_data 输出的是AIMessage类型的  不是分块流式输出   作者这是怎么回事

**State:** OPEN
**Created:** 2025-09-13T08:33:48Z
**URL:** https://github.com/bytedance/deer-flow/issues/579

### Description

以下是我重构的原始部分代码    
async for agent, mode, event_data in graph.astream(  
        input=initial_state,
        config={
            "thread_id": thread_id, 
            "max_plan_iterations": max_plan_iterations, 
            "max_step_num": max_step_num,  
        },
        stream_mode=["updates", "...

### Analysis

This issue relates to deerflow. Related to **installation** or **setup**. Impact assessment needed based on labels and community engagement.

## Issue #573: [错误] 流式读取中断 (ChunkedEncodingError): Response ended prematurely

**State:** OPEN
**Created:** 2025-09-12T09:07:13Z
**URL:** https://github.com/bytedance/deer-flow/issues/573

### Description

[错误] 流式读取中断 (ChunkedEncodingError): Response ended prematurely 


import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

def make_streaming_request_with_retry():
    url = "http://10.63.129.228:8286/api/chat/stream"
    json_payload = {
        "m...

### Analysis

This issue relates to deerflow. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #549: 请问，是不是没有做消息压缩或裁剪功能？

**State:** OPEN
**Created:** 2025-08-29T09:11:31Z
**URL:** https://github.com/bytedance/deer-flow/issues/549

### Description

现在有这样一个情况，运行一个分析问题时，大模型给出了5次调用web_search的工具调用，每次调用会搜索出3个网页结果，如果其中某些网页内容过多，这样最终AI的message就会很多，就会超过大模型的token，就会报openai.BadRequestError: Error code: 400 - {'error': {'code': 'InvalidParameter', 'message': 'Total tokens of image and text exceed max message tokens. Request id: 021756453937251fef43cebbc3e...

### Analysis

This issue relates to deerflow. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Issue #542: Is it possible to reduce input token without compromising quality?

**State:** OPEN
**Created:** 2025-08-24T13:50:50Z
**URL:** https://github.com/bytedance/deer-flow/issues/542

### Description

<img width="829" height="625" alt="Image" src="https://github.com/user-attachments/assets/3ba96a55-8579-447a-befb-56d8177f3fc6" />

As can be seen in the post below, when I start a deep research process with the above settings, there is an incredible inflow of input tokens, which causes each deep re...

### Analysis

This issue relates to deerflow. Impact assessment needed based on labels and community engagement.

## Issue #532: [Feature Request] 能帮忙支持连续对话多次 deep research 么？（有偿实现）

**State:** OPEN
**Created:** 2025-08-22T06:04:46Z
**URL:** https://github.com/bytedance/deer-flow/issues/532

### Description

我们项目是基于 deerflow 的但是想支持在一个 session 里面实现连续多次的 deep research, 就是随着
持续的补充额外信息的，持续的进行 deep research ;  先在的实现貌似会有上下文的错乱；不知道官方
会打算支持这个么？

另外，我们是个AI Agent startup, 我们也愿意有偿招人实现这个功能（兼职/全职，base 杭州），如果你
对 deer-flow 比较熟悉对 AI Agent 创业感兴趣的话，可以联系我聊聊；  miletus@chromium.org

### Analysis

This issue relates to deerflow. Appears to be a **feature request**. Impact assessment needed based on labels and community engagement.

## Issue #531: JavaScript heap out of memory

**State:** OPEN
**Created:** 2025-08-22T01:31:20Z
**URL:** https://github.com/bytedance/deer-flow/issues/531

### Description

pnpm dev 报错，node版本23.1.0 Linux系统

--- Last few GCs --->

[58283:0x7e91000]    14451 ms: Scavenge 10230.6 (10239.3) -> 10230.6 (10243.3) MB, pooled: 0 MB, 1.59 / 0.00 ms  (average mu = 0.977, current mu = 0.931) allocation failure; 
[58283:0x7e91000]    14473 ms: Mark-Compact (reduce) 10241.4 (10254....

### Analysis

This issue relates to deerflow. Appears to be a **bug report** or **error**. Impact assessment needed based on labels and community engagement.

## Recommendations

- Review 10 new issues above
- Prioritize based on labels and community response
- Consider backlog items for high-priority patterns

