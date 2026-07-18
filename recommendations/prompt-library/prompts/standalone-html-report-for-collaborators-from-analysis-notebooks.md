---
title: Standalone HTML report for collaborators from analysis notebooks
scenarios: reporting,research,collaboration
tags: html,notebook,figures,mock-data,open-questions
source: claude-code
session:
date: 2026-05-12
---

# Standalone HTML report for collaborators from analysis notebooks

> Use when you need a shareable artifact for people who will not open your notebooks, but you still want the notebooks to be the source of truth.

## Original

```text
请给我一个英文 HTML 报告用于给合作者展示（不要花里胡哨），包含至少以下内容：

<round> 目前都做了什么；数据分析（包含 <notebook-A> 里的数据分布图，特别是不均匀分布和有强烈特征的图；此外在本 HTML 和 notebook 里加入同一个"每个特征缺失数量"的分析图；再在 HTML 里加入 notebook 的相对链接）；结果分析（主要来自 <notebook-B>，特别是 <cell> 的结果图表，以及 <N> 张 <method> 分析图（补上 <model-A> 的 summary 图和 <model-B> 的两张图），然后插入 notebook 链接）；未来最有希望的研究方向（除了之前所讨论的，可以简单论述下预训练模型 finetuning / 蒸馏可不可行，以及对缺失值的处理方案）；最后引出相关的、需要合作者明确的问题（例如坐标的含义，实际需要的输入输出特征是什么）。

注意新增的图依然先用 mock data 验证，我自己跑真实数据一键生成新图。
```

## Optimized

```text
Produce a single self-contained HTML report in English for collaborators. Plain and readable, no
decoration.

Sections, in order:
1. What this round actually did.
2. Data analysis. Pull the distribution figures from <notebook A>, especially the skewed ones and any
   with a strong visible structure. Add a missing-values-per-feature figure, and add that same figure
   to the notebook so the two stay in sync. Link the notebook by relative path.
3. Results. Pull from <notebook B>, including <the specific outputs>. Fill the gaps in the current
   figure set: <name the missing figures explicitly>. Link the notebook.
4. Most promising directions next. Beyond what we already discussed, assess briefly whether
   <alternative approach A> and <alternative approach B> are viable here.
5. Open questions for the collaborators. Be specific and answerable — the things only they can settle,
   such as <example of a domain question>.

Generate every new figure against mock data first so I can check the plotting code. I will run the
real data myself to produce the final images.
```

## When to use

Use when you need a shareable artifact for people who will not open your notebooks, but you still want
the notebooks to be the source of truth.

- Periodic updates to a collaborator, supervisor or external partner.
- When the point of the report is as much to ASK as to tell. Section 5 is what turns a status update
  into a decision the collaborator can make.
- When figure code should be reviewable before it touches real data.

## When NOT to use

Skip the mock-data step when the figure only makes sense with real values, such as an outlier plot.
Verify the code some other way instead.

Do not use it for an internal update where a message with two charts would do.

Do not use it when the data cannot leave a controlled environment. A self-contained HTML file with
embedded figures is exactly the artifact that leaks.
