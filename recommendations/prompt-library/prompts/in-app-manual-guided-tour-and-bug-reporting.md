---
title: In-app manual, guided tour and bug reporting
scenarios: product,onboarding,docs,ui
tags: manual,walkthrough,bug-report,testing
source: claude-code
session:
date: 2026-07-06
---

# In-app manual, guided tour and bug reporting

> Use when a product is about to go to testers who are not the people who built it.

## Original

```text
我们之前有个文档专门测试所有的功能，包括流程、截图、mermaid 图等。下面，给所有组别用户实现以下几个功能：

1. 在界面左边添加一个手册功能，这个手册里是所有的功能。功能包含图文并茂的使用流程，包括说明、截图、mermaid 图等。这个手册是专门用于测试用的，所以要展示正常的情况是什么样子，常见有问题的情况是什么样子，常见 QnA 等。

2. 每个功能加一个动态引导，引导测试人员或用户一步一步使用该功能（用户跟着引导操作，系统判断是否正确并决定是否推进下一步）。每个引导功能都可以在手册的对应功能里激活重放。

3. 加一个报错功能给 admin 和 test 组用户。用户可以打字、插入（多个）图片 / 截图，并且给截图一个手绘板功能方便用户编辑。截图时给一个内置截图工具，同时隐藏报错功能方便用户截图（可以选择不隐藏，防止报告的是报错功能本身的错误），截图好后再复现报错功能并自动插入。如果是 admin 账号，则提交时强制要求用户写自己的名字（因为这个账户会给不同的人），如果是其他账号则自动填入账号名（可修改）。这些内容在后台写入 <repo> 的 issue，内容包含此人的信息（除非 ta 是通过第三方登录的，则直接用那个账号），名字，使用的账号名，并且说明这个 issue 来自 <product> 的报错功能。写 issue 的功能你先调研下可不可行，以及有无更好方案。

实现以上功能。注意，为了保证时效性（我要尽快发布平台测试），先完成以上功能并且只实现对 <one feature> 的手册和引导。完成后对这些新功能完整测试，测试无误后汇报给我，然后你再处理其他所有功能的手册和引导。请对这些内容的设计进行详细调研分析和优化，并贴合我们的平台设计。
```

## Optimized

```text
Add three linked capabilities to <product>, for all user groups.

1. A manual, opened from <location in the UI>, covering every feature. Each entry shows the flow with
   text, screenshots and a mermaid diagram. It is written for testing, so it must show what CORRECT
   looks like, what the common failure states look like, and a short FAQ.

2. A guided walkthrough per feature: the user follows the steps, and the app checks each step before
   advancing. Every walkthrough is replayable from that feature's manual entry.

3. A bug reporter for <privileged groups>. The user can type, attach several images, and annotate
   each with a simple drawing tool. Provide a built-in capture tool that hides the reporter itself
   while capturing (with an option to keep it visible, so the reporter's own bugs can be reported),
   then restores it and inserts the image. Shared accounts must prompt for the reporter's real name;
   individual accounts prefill it, editable. Submissions become issues in <tracker>, tagged as coming
   from the in-app reporter and carrying the submitter's identity.
   First check whether writing to <tracker> that way is actually feasible, and whether a better route
   exists. Report the finding before building it.

Sequencing, because a release is waiting: build all three, but ship the manual and walkthrough for
<one feature> only. Test that slice fully, report, then extend to the remaining features.

Research the design of each part and align it with the existing product patterns before implementing.
```

## When to use

Use when a product is about to go to testers who are not the people who built it. It bundles the
three things testers always need at once: a reference for what correct looks like, a hands-on path
through each feature, and a low-friction way to report what broke.

- Handing a build to a mixed group of testers.
- Testers are non-technical, so "file a GitHub issue" is not a realistic ask on its own.
- You want the first slice shipped before the full manual exists, which the explicit sequencing gives you.

## When NOT to use

Skip it while the UI is still changing weekly. Screenshots and step-by-step checks are the first
things a redesign invalidates.

Skip the bug reporter when your testers already live in your tracker. Building a second path to the
same place splits the reports.

Do not use it for an internal tool with under a handful of users. A direct conversation beats a
walkthrough engine at that scale.
