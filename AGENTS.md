# Project: Sales Analytics Platform

## Layers
- BRONZE = raw, immutable. Never modify.
- SILVER = typed and cleaned. Built by $stage-table.
- GOLD = business marts. Built by gold-mart-builder.

## Conventions
- snake_case columns; comment every table and column
- Dynamic Tables with TARGET_LAG = '1 hour', WAREHOUSE = COCO_WH
- Show DDL for approval before executing