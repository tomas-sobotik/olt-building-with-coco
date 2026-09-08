
# Build a `gold-mart-builder` agent

Let's define one simple custom subagent, store it in `.cortex/agents/` and delegate a single task to it. We are going to build an agent for building a gold table from our silver layer.

From previous chapter we have a `SILVER` schema containing SILVER layer dynamic tables.

Let's create a GOLD schema now:
```CREATE SCHEMA IF NOT EXISTS COCO_COURSE.GOLD; ```

Our agent will build a `CUSTOMER_360` table with one row per customer together with our order summary:

## CoCo prompt to build an agent for us
```
Create a custom subagent for this project called gold-mart-builder. Put it in .cortex/agents/gold-mart-builder.md so it is committed with the repo.
Its job: build Gold-layer tables in COCO_COURSE.GOLD from the Silver layer. Give it the snowflake_sql_execute, Read and Write tools.
The system prompt should tell it to: inspect the relevant Silver tables first, write a CREATE OR REPLACE TABLE statement, add a table comment, execute it, then report the row count and a 5-row sample. It should state any assumption it makes rather than guessing silently. Agent should not modify anything in the BRONZE or SILVER schemas. 
 ```

 ## Try the agent

 ```
 Use gold-mart-builder agent to build GOLD_CUSTOMER_360 table from SILVER_CUSTOMERS and SILVER_ORDERS.
 ```