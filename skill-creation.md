## Skill exercise
We are going to build a `stage-table` skill. Use CoCo to author a custom skill that turns a raw Bronze table into a standardized Silver Dynamic Table, commit it under .cortex/skills/.

As a first prerequisite to make CLI work let's set the cross region reference for agent connection. I use AWS_EU as a value since my Snowflake account is in provisioned in one of the AWS EU regions. 

```
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'AWS_EU';
```

### Prompt to create sample data to work with

Create a small sales/e-commerce Bronze (raw) layer in COCO_COURSE.BRONZE on Snowflake. Everything lands as raw strings, exactly as an ingestion tool would drop it. Create these three tables with these exact names, columns, and column order — all columns STRING except the final load timestamp which is TIMESTAMP_NTZ:

BRONZE_CUSTOMERS (CUSTOMER_ID, FIRST_NAME, LAST_NAME, EMAIL, COUNTRY, SIGNUP_DATE, RAW_LOADED_AT)
BRONZE_ORDERS (ORDER_ID, CUSTOMER_ID, ORDER_TS, ORDER_STATUS, CURRENCY, ORDER_AMOUNT, RAW_LOADED_AT)
BRONZE_ORDER_ITEMS (ORDER_ITEM_ID, ORDER_ID, PRODUCT_NAME, QUANTITY, UNIT_PRICE, RAW_LOADED_AT)

Relationships: BRONZE_ORDERS.CUSTOMER_ID references BRONZE_CUSTOMERS.CUSTOMER_ID; BRONZE_ORDER_ITEMS.ORDER_ID references BRONZE_ORDERS.ORDER_ID.

Insert realistic sample rows: 20 customers, ~50 orders, ~120 order items, with valid foreign keys. Make the raw data intentionally messy so a staging step is meaningful: SIGNUP_DATE and ORDER_TS as strings, ORDER_AMOUNT/UNIT_PRICE/QUANTITY as numeric strings, and ORDER_STATUS in mixed case (e.g. "shipped", "Cancelled", "PENDING"). Then show me a 5-row sample of each table.

Fixed target relationships
BRONZE_CUSTOMERS 1---* BRONZE_ORDERS 1---* BRONZE_ORDER_ITEMS

### Prompt to create a skill
Help me build a project skill called stage-table. It takes one input — a Bronze table name like BRONZE_ORDERS — and generates a Silver Dynamic Table in COCO_COURSE.SILVER. 

Conventions it must always apply: 
- rename all columns to snake_case; 
- cast raw strings to proper types (dates, timestamps, numbers); 
- add a surrogate key <entity>_sk = HASH(<natural_key>); 
- add dw_load_ts = CURRENT_TIMESTAMP() and source_system = 'SALES_APP'; 
- uppercase status columns; 
- add table and column comments. 

It should inspect the source first, show the DDL for approval before executing, then validate row-count parity and surrogate-key uniqueness. Put it under temp/skills/ for validation. I will move it to correct location after validation.

### How to check installed skills
`/skill` 


### Try the custom skill
Run `$stage-table` skill and watch how CoCo follows the istructions. Sample prompt: 

```use stage-table skill to create a silver dynamic table for all bronze tables```
