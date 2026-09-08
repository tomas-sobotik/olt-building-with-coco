# Guardrails exercise

Let's start by adding a generic `AGENTS.md` file to our repo with basic informations about our project which are always loaded and CoCo knows the context automatically. File also contains information that our bronze layer is immutable and can't be updated.

This is just a soft guidance. It will not stop us to modify the bronze table anyway.

Because of that let's try to add a hook as which will block such action and will be a true guardrail.

Add following AGENTS.MD file into your repo:
```
 Project: Sales Analytics Platform

## Layers
- BRONZE = raw, immutable. Never modify.
- SILVER = typed and cleaned. Built by $stage-table.
- GOLD = business marts. Built by gold-mart-builder.

## Conventions
- snake_case columns; comment every table and column
- Dynamic Tables with TARGET_LAG = '1 hour', WAREHOUSE = COCO_WH
- Show DDL for approval before executing

```

Let's try to modify the bronze table now with a prompt:
```
Add a new column called temp_id to BRONZE_ORDERS
```

## Defining the hook
Let's use a coco to create it for us. Here is a prompt:

```
Create a PreToolUse hook for this project. Matcher: sql*. Type: prompt.
The hook should ask: "Does this SQL statement modify data or structure in the BRONZE schema? BRONZE is immutable raw data — it must never be modified. If yes, block it and explain why."
Save the hook configuration under .cortex/settings.json so it's committed with the repo and applies to anyone who clones it.
```

Here is also `.cortex/settings.json` file for a reference. You can create it also manually:

```
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "sql.*",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Does this SQL statement modify data or structure in the BRONZE schema? BRONZE is immutable raw data — it must never be modified. If yes, block it and explain why.",
            "enabled": true
          }
        ]
      }
    ]
  }
}
```