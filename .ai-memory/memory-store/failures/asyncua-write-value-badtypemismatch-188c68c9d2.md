---
store_path: failures/asyncua-write-value-badtypemismatch-188c68c9d2
title: "asyncua write_value BadTypeMismatch when writing int to UInt16 or Double node wi"
summary: "asyncua write_value BadTypeMismatch when writing int to UInt16 or Double node wi"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-08-12T08:59:14-04:00"
occurrences: 1
error_signature: "asyncua write_value badtypemismatch when writing int to uint<n> or double node without explicit variant wrapper"
---

## Occurrence 1 — 2026-08-12T08:59:14-04:00

**Error:**
asyncua write_value BadTypeMismatch when writing int to UInt16 or Double node without explicit Variant wrapper

**Fix:**
Wrap variables explicitly using ua.Variant(value, ua.VariantType.UInt16) or ua.VariantType.Double before calling node.write_value()
