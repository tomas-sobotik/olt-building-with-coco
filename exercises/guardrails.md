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
Create a hook that protects the BRONZE schema from modifications while still allowing reads.

  I need a PreToolUse hook that blocks any SQL statement that would modify data or structure in the BRONZE schema (things like
  ALTER, DROP, INSERT, UPDATE, DELETE, MERGE, CREATE, or TRUNCATE), but still allows SELECT queries to read from BRONZE tables.

  The hook should:

  • Be a command hook (not a prompt hook — command hooks enforce at the system level and can't be overridden)
  • Use a shell script that reads the SQL from the tool input, checks if it's both a modification statement and targets BRONZE,
   and blocks it if so
  • Block by exiting with code 2 and writing the reason to stderr
  • Allow everything else by exiting with code 0
  • Only fire on the sql_execute tool

  Put the shell script in .cortex/hooks/ and register the hook in .cortex/settings.json under the hooks key.

```

You need to restart a CoCo session to get the hook loaded. Run `/restart` and then you can run `/hooks` to confirm the PreToolUse hook is listed and enabled.

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