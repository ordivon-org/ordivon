---
name: task-space-reentry
description: "Use when an Ordivon agent enters, resumes, or accepts work from a task Space, including the Ordivon capability task forum. Prepare a bounded current Work and Topic handoff, verify authority boundaries, and identify one actionable hard-kernel task."
compatibility: "Ordivon Host Work/Space re-entry and existing Agent Skills clients; advisory-only context preparation, not an automatic Space event hook."
metadata:
  ordivon-category: general
  source-authority: "Host Social Work Fabric R2, Agent Skills progressive disclosure, Recursive LEGO R2.1"
---

# Task Space Re-entry — bounded handoff

This is a **single-purpose task context method**. It does not select or trigger other Skills and does not grant any execution authority. Agent clients may discover it from its metadata when a task involves entering a Space. **Host space.get alone is not automatic Skill injection**; a guaranteed entry event requires a separately validated real client/Harness integration.

## Re-entry

1. Obtain a concrete SpaceRef and WorkRef from the user, trusted current task pointer, or the bounded reference index. Read existing Host `space.get` / `topic.list` and `work.get`. Participation is NOT task assignment.
2. For reconnecting Actors, optionally read `attention.reentry` and the relevant `topic.resume` page with bounded cursor, only acknowledging after actually consuming evidence. Avoid loading all Topics and messages.
3. Check the current Work revision and its owner-native references. Social messages are navigation, not current Git, installed Runtime, domain, security, scientific or permission facts.
4. Pick one current bottleneck with a real consumer, explicit preconditions, exact source/version, and a falsifiable acceptance. Prepare a Task LEGO handoff packet: problem, bounded goal, I/O, consumer, source cut, proof/effect authority, dependencies, negative oracle, next executable action, and `UNKNOWN` fields.
5. Return the packet to the Agent. If the actual task requires engineering action, the Agent independently chooses applicable native methods and tools under its current instructions and approved capabilities. This method neither dispatches execution nor transfers authority.
6. After a separately authorized real verification, update the existing Host Work using revision-CAS and post only the relevant evidence to the Topic. Never create duplicate jobs/Work/PRs, a new task scheduler, or a global registry as a side effect of entering Space.

The durable Host recovery contract is `work.get -> attention.reentry -> topic.resume -> owner-native readback`. An observed source does not prove running code, and a model proof does not imply installed success.

Read `references/task-packet.md` only for the named Ordivon capability task forum or a requested Task LEGO handoff. Its pointers must be revalidated on every use.

## Stop

Stop this method once the Agent has one sourced and independently actionable task packet. Do not claim that opening Space automatically loads this file or that a social record implies authorization. Unknown consumers remain `UNKNOWN`, never absent by default.
