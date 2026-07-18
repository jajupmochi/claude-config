---
title: Separate a tuned hyperparameter from an ablation sweep
scenarios: research,experiments,config
tags: hyperparameter,ablation,sweep,scope-control
source: claude-code
session:
date: 2026-06-11
---

# Separate a tuned hyperparameter from an ablation sweep

> Use when designing configuration for research code and a parameter has to serve two purposes: something you optimize, and something you study.

## Original

```text
首先我想确认一下：<parameter-A> 和 <parameter-B> 这两个参数是可以自由定义的吗？还是说一旦数据和 model 给定，这两个参数就确定了？

如果可以自由定义的话，那其实两个情况都得有。一种就是像前面的 optimizer 那样，我可以直接对它进行 tuning —— 这种情况就是我正常的实验进行对比的时候要用。第二种情况就是你上面说的 sweep：这种情况下我其实要做的是一个 ablation 的实验，或者说对这个参数进行影响分析的实验；在这种情况下的话，确实需要在外部进行 sweep，然后同时固定内部的那个 tuning，让它直接使用外部 sweep 的参数。

请你先完成第一种模式，第二种模式先记下来，后面再说。而且第二种模式我们会做一个新的入口，不和现在的入口重合，专门做参数分析。
```

## Optimized

```text
First, a factual question before any code: are <parameter A> and <parameter B> free to choose, or are
they determined once the dataset and model are fixed? Answer that before proposing a design.

If they are free, we need both modes, and they must not be confused:

Mode 1, tuning. The parameter is searched inside the normal run, like the optimizer settings already
are. This is what a regular comparison experiment uses. Build this one now.

Mode 2, ablation sweep. The parameter is swept OUTSIDE the run, and the inner search is pinned so it
uses the swept value verbatim. This measures the parameter's effect rather than optimizing it. Record
this mode in the backlog with the design above, and give it its OWN entry point when we build it — it
must not share the entry point with mode 1.

Implement mode 1 only. Confirm the mode 2 note is written down before you finish.
```

## When to use

Use when designing configuration for research code and a parameter has to serve two purposes:
something you optimize, and something you study.

- Setting up a hyperparameter search that will later need an ablation over the same knob.
- When you have caught yourself unsure whether a number came from tuning or from a fixed sweep value.
- When the value may in fact be determined by the data, which is why the first question comes before
  the design.

The separate entry point is what stops an ablation from silently re-tuning underneath you and
reporting an effect that is really the search.

## When NOT to use

Skip it when the parameter is genuinely fixed by the data or the architecture. Then there is nothing to
tune and nothing to sweep, and building both modes creates a knob that does not change behaviour.

Skip it when you will never ablate the parameter. Two modes for a value nobody studies is dead
configuration.

Do not implement both modes at once. The value here comes from shipping mode 1 and recording mode 2,
so that the second entry point gets designed when you actually need it.
