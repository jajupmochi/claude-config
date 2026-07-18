---
title: Inspect a dataset schema without reading the data
scenarios: data-platform,privacy,analysis
tags: schema,confidentiality,validation,context-hygiene
source: claude-code
session:
date: 2026-07-05
---

# Inspect a dataset schema without reading the data

> Use whenever you need an agent to reason about a dataset that it must not see.

## Original

```text
请你看一下 <source-A> 里的数据文件，和 <source-B> 下的几个 csv 文件的区别是什么？注意，这里只允许你使用代码读取这些文件的框架，例如行名列名等等，不允许读具体的数据，这些数据也不允许进入到上下文中。

确认清楚后分析现在的数据平台是否能够输入这些数据。我指的是每一项数据，而且是否对这些数据输入的格式等等进行了合适的限制或者自动规归化。同时是否包含用户进行 verification 和确认的功能（包含各个层级的，例如每一项具体的数据、每一行 item、每一个表单、所有的数据等等）。

然后告诉我在数据平台的设计中，应该参照这里的表单进行设计，还是我们实际的数据库 sql 里的表单设计，以及这两个表单是否对得上。
```

## Optimized

```text
Compare the data in <source A> with <source B>.

Constraint, and this one is absolute: you may only read the STRUCTURE with code — column names, row
counts, dtypes, null counts, distinct-value counts. Do not read individual values, do not print
sample rows, and do not let any record content enter the conversation context. If a check would
require seeing values, describe the check you would run instead of running it.

With the structure established, answer:
1. Can the platform currently ingest every one of these fields? Go field by field, not in aggregate.
2. Is each field validated or normalized on entry, and how?
3. Is there a verification and sign-off step at every level: the individual value, the row, the
   submitted form, and the batch?
4. Should the platform's schema follow this file's shape or the database schema we already have,
   and do those two agree? Where they disagree, list the mismatches.
```

## When to use

Use whenever you need an agent to reason about a dataset that it must not see. The read-structure-only
constraint is the whole point, and stating it as a hard rule rather than a preference is what makes it
hold.

- Confidential, personal or client data where the file is available but the contents are restricted.
- Schema and pipeline design work, where field names and types are sufficient.
- Any time a large file would otherwise flood the context window.

## When NOT to use

Skip it when the actual values are the question. Data-quality work, outlier hunting and encoding bugs
all require looking, so use a sanitized or synthetic extract instead of pretending the constraint
still holds.

Skip it for data you have already published or that is public. The constraint costs accuracy and buys
nothing there.

Do not rely on this prompt alone for regulated data. It is an instruction, not an enforcement
boundary — pair it with access controls that make the unsafe read impossible.
