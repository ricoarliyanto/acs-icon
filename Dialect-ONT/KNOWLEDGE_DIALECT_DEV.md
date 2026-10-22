# Dialect Development & Troubleshooting Knowledge Base

This document summarizes strict rules and patterns for developing and debugging Device Dialects (Groovy/DSL based), specifically derived from the Huawei EG8041V5 and Alcatel development sessions.

## 1. Syntax & Compilation Limitations

### A. No Local Variables (`val`/`def`)

**Rule:** Do NOT use `val` or `def` inside expression blocks (`"""${ ... }"""`), neither in `read_converter` nor in `virtualPatching`.
**Reason:** The internal Groovy/Scala compiler environment often rejects local variable definitions in these contexts, leading to `not found: value val` errors.
**Solution:** Use inline expressions or chaining.

- **Bad:**
  ```groovy
  expression = """${
     val mac = node.value.toUpperCase()
     dm.Hosts.filter(x => x.MAC == mac)...
  }"""
  ```
- **Good:**
  ```groovy
  expression = """${
     dm.Hosts.filter(x => x.MAC == node.value.toUpperCase())...
  }"""
  ```

### B. Handle `Option` Types Explicitly (or Avoid Them)

**Rule:** Avoid using `.find(...)` directly if you aren't sure of the return type inference. `getOrElse` on a String or implicit conversion failures are common.
**Solution:** Use `.filter(...).map(...).join` pattern.

- **Pattern:** `keys.filter(condition).map(target_value).join`
- **Why:** `join` safely returns a String. If no match, it returns `""` (empty string). This avoids runtime null pointer exceptions or `Option` wrapping issues.

## 2. Parameter Mapping Strategies

### A. The "Hybrid" Strategy for Complex Lookups

**Scenario:** You need to display a value (e.g., RSSI) that lives in a different table (e.g., `Hosts`) than the device object (e.g., `WiFi.AssociatedDevice`), and you need a key (e.g., MAC) to join them.

**Strategy:**

1.  **Standard Mapping:** Map the parameter to the "Key" value first.
    - `SignalStrength.real = "...AssociatedDevice.%i.MACAddress"`
2.  **Virtual Patching:** Use `%patch-value` to transform that key into the desired value.
    - Target: `virtualPatching.patching...AssociatedDevice.%any`
    - Logic: Access `node.value` (which is now the MAC), perform lookup, return result.

**Example:**

```groovy
# 1. Mapping
AssociatedDevice.%i {
  SignalStrength.real = "...MACAddress"
}

# 2. Patching
AssociatedDevice.%any {
  SignalStrength {
    %patch-value = """${
       dm.LookupTable.filter(k => k.MAC == node.value).map(v => v.RSSI).join
    }"""
  }
}
```

### B. `read_converter` vs `virtualPatching`

- **read_converter:** Best for simple formatting (e.g., bytes to KB, status code to string).
  - _Warning:_ deeply nested structures inside `read_converter` (e.g., `WiFi.%i.AssociatedDevice.%i`) are prone to parsing ambiguity. Flattened quoted keys like `"WiFi.%i.SubNode.%i.Param"` are safer but not always supported.
- **virtualPatching:** Best for structural changes, complex lookups, or fixing "missing" parameters.
  - Use `%patch-value` to transform existing values.
  - Use `%force-value` to create values from scratch (requires `%force-object-exists = true` or strict tree definition).

### C. `%override-tree` Pitfall

**Warning:** If you use `%override-tree = true`, you **MUST** explicitly define EVERY parameter you want to appear in that subtree. Any parameter not listed will effectively be deleted from the ACS's view, causing "missing data" in the UI even if the standard mapping exists.

## 3. Debugging Techniques

### A. The Static Force

If a value isn't appearing:

1.  Set `%force-value = "DEBUG_STRING"` or a static number (e.g., `-55`).
2.  If it appears: The mapping/patching path is correct; the logic inside the expression is broken (e.g., matching failed).
3.  If it doesn't appear: The mapping/patching path is wrong, or the parameter structure is invalid (typo in key name, wrong hierarchy).

### B. "No Data" in UI

- Check **Data Types**: The UI might expect an Integer. If you send a String "-55", it might reject it. Use `%force-type = "xsd:int"`.
- Check **Structure**: Ensure valid hierarchy (e.g., `AssociatedDevice` inside `WiFi.2`).

## 4. Hierarchy Management

- **Brace Counting:** Automated edits often break brace nesting. Always verifying the `}` count is critical.
- **Placement:** Place global patches (patches using absolute paths starting with `root...`) at the **END** of the file to avoid breaking the indentation/context of the main blocks.
