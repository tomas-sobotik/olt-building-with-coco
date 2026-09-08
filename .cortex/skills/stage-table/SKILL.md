---
name: stage-table
description: "Generate a Silver Dynamic Table from a Bronze source table in COCO_COURSE. Use when: staging a bronze table, promoting to silver, creating a silver dynamic table, stage-table, stage table, silver layer. Input: a Bronze table name like BRONZE_ORDERS."
---

# Stage Table: Bronze to Silver Dynamic Table

## Purpose

Takes a single Bronze table name (e.g. `BRONZE_ORDERS`) and generates a Silver Dynamic Table in `COCO_COURSE.SILVER` that applies standard transformations and governance conventions.

## Conventions

All Silver tables produced by this skill MUST apply:

1. **Snake-case columns** — rename every column from `SHOUTCASE` or `camelCase` to `snake_case`
2. **Type casting** — cast raw VARCHAR columns to proper types:
   - Date patterns → `DATE`
   - Timestamp patterns → `TIMESTAMP_NTZ`
   - Numeric patterns → `NUMBER` or `FLOAT`
   - Boolean patterns → `BOOLEAN`
3. **Surrogate key** — add `<entity>_sk` column as `HASH(<natural_key_columns>)` (first column or obvious PK)
4. **Audit columns**:
   - `dw_load_ts TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()`
   - `source_system VARCHAR DEFAULT 'SALES_APP'`
5. **Status normalization** — `UPPER()` any column whose name contains "status"
6. **Comments** — add a `COMMENT` on the table and on every column

## Workflow

### Step 1: Identify the Source

Ask the user for the Bronze table name if not provided. The fully-qualified source is:
```
COCO_COURSE.BRONZE.<TABLE_NAME>
```

### Step 2: Inspect the Source Schema

Run:
```sql
DESCRIBE TABLE COCO_COURSE.BRONZE.<TABLE_NAME>;
```

Also sample rows to infer actual data types:
```sql
SELECT * FROM COCO_COURSE.BRONZE.<TABLE_NAME> LIMIT 10;
```

Use the column names, current types, and sample values to decide:
- Which columns are dates/timestamps (look for patterns like `2024-01-15`, ISO timestamps)
- Which columns are numeric (integers, decimals)
- Which columns are booleans (`true`/`false`, `0`/`1`, `Y`/`N`)
- Which column(s) form the natural key (typically `*_ID` or the first column)
- Which columns contain status values (name contains `status`)

### Step 3: Derive the Silver Table Name

Strip the `BRONZE_` prefix and prepend `SILVER_`:
- `BRONZE_ORDERS` → `SILVER_ORDERS`
- `BRONZE_CUSTOMER_ADDRESSES` → `SILVER_CUSTOMER_ADDRESSES`

Entity name for the surrogate key is the singular noun:
- `ORDERS` → `order_sk`
- `CUSTOMERS` → `customer_sk`
- `CUSTOMER_ADDRESSES` → `customer_address_sk`

### Step 4: Generate DDL

Build a `CREATE OR REPLACE DYNAMIC TABLE` statement with:
- Target: `COCO_COURSE.SILVER.<SILVER_TABLE_NAME>`
- `TARGET_LAG = '1 hour'` (sensible default; mention user can adjust)
- `WAREHOUSE = COCO_WH`
- Column transformations per conventions above
- Table comment summarizing lineage

**Template structure:**
```sql
CREATE OR REPLACE DYNAMIC TABLE COCO_COURSE.SILVER.<SILVER_TABLE_NAME>
  TARGET_LAG = '1 hour'
  WAREHOUSE = COCO_COURSE_WH
  COMMENT = 'Silver layer: cleaned and typed <entity> data sourced from COCO_COURSE.BRONZE.<TABLE_NAME>'
AS
SELECT
    HASH(<natural_key_col>) AS <entity>_sk,
    <col_1_renamed> :: <CAST_TYPE> AS <col_1_snake>,
    -- ... all columns with casts and renames ...
    UPPER(<status_col>) AS <status_col_snake>,
    CURRENT_TIMESTAMP() AS dw_load_ts,
    'SALES_APP' AS source_system
FROM COCO_COURSE.BRONZE.<TABLE_NAME>;
```

Then column comments:
```sql
COMMENT ON COLUMN COCO_COURSE.SILVER.<TABLE>.<COL> IS '<description>';
```

### Step 5: Present DDL for Approval

**STOPPING POINT** — Show the complete DDL to the user and ask:
- "Does this look correct? Should I execute it?"
- Highlight any assumptions made (type casts, natural key choice)

Do NOT execute until the user explicitly approves.

### Step 6: Execute DDL

Run the approved DDL statements via `sql_execute`.

### Step 7: Validate

Run two validation checks:

**Row-count parity:**
```sql
SELECT
    (SELECT COUNT(*) FROM COCO_COURSE.BRONZE.<TABLE_NAME>) AS bronze_count,
    (SELECT COUNT(*) FROM COCO_COURSE.SILVER.<SILVER_TABLE_NAME>) AS silver_count;
```
Counts must match exactly.

**Surrogate-key uniqueness:**
```sql
SELECT <entity>_sk, COUNT(*) AS cnt
FROM COCO_COURSE.SILVER.<SILVER_TABLE_NAME>
GROUP BY <entity>_sk
HAVING cnt > 1;
```
Must return zero rows.

### Step 8: Report Results

Present a summary:
- Table created: `COCO_COURSE.SILVER.<SILVER_TABLE_NAME>`
- Row count: N rows
- Surrogate key: unique (confirmed)
- Columns: list with types

## Stopping Points

1. **After Step 5** — DDL approval before execution (MANDATORY)
2. **After Step 7** — If validation fails, stop and report the issue

## Error Handling

- If source table doesn't exist → tell the user; list available Bronze tables
- If SILVER schema doesn't exist → offer to create it
- If row counts don't match → investigate; dynamic tables may still be initializing — wait and retry once
- If SK has duplicates → the natural key choice was wrong; ask user to pick the correct key columns

## Output

A fully operational Silver Dynamic Table with:
- Clean snake_case column names
- Proper data types
- Surrogate key
- Audit columns
- Table and column comments
- Validated row parity and key uniqueness
