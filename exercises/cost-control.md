# Cost control exercise
Let's use CoCo to build a streamlit dashboard for us. It will track CoCo's token and credit consumptions across all interfaces. 
Since we work in trial account and might not have any or very little data related to token consumption, let's also add a dummy data in case nothing is found in system views.

Here is prompt for CoCo:

```
Build a Streamlit-in-Snowflake app called CoCo Cost Overview that reports Snowflake CoCo token consumption and cost.
Data sources — these three SNOWFLAKE.ACCOUNT_USAGE views, one per interface: CORTEX_CODE_CLI_USAGE_HISTORY, CORTEX_CODE_DESKTOP_USAGE_HISTORY, and CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY. They share a schema: USER_ID, USAGE_TIME, TOKENS, TOKEN_CREDITS, REQUEST_ID, plus TOKENS_GRANULAR and CREDITS_GRANULAR (VARIANT columns holding the per-model breakdown).

Note: the CLI and Snowsight views expose only USER_ID, not a user name — join to SNOWFLAKE.ACCOUNT_USAGE.USERS on USER_ID where DELETED_ON IS NULL, and display first + last name, falling back to NAME when those are empty.

Sidebar filters
Time period: Last Day / Last 7 Days / Last 30 Days / Custom date range
Multi-select filter by user, listing only users who appear in the usage views

Layout
Per-interface metric rows — CLI, Desktop, Snowsight — each showing tokens, credits, and cost in USD. Then a combined total row.
Token consumption over time: one line chart per interface, side by side, daily grain.

Cost by model — flatten CREDITS_GRANULAR to get per-model credits, shown as a bar chart plus a table. This matters because model choice is the biggest cost driver.

Per-user table combining all three interfaces: name, email, tokens and credits per interface, totals, and total cost in USD, sorted by cost descending. Paginate 20 rows at a time with a "Show More" button.

Details
Set a CREDIT_PRICE_USD constant at the top (default 2.20) and use it for all USD conversion — credit price is regional, so it must be easy to change.
Use get_active_session() from snowflake.snowpark.context.

Format tokens with thousands separators, credits to 4 decimals, USD to 2.

Handle empty result sets with st.info(...) rather than erroring — these views lag 45 minutes to 2 hours, so an empty period is normal.
Wide layout, charts built with Altair, and interactive tooltips.

Fallback strategy:
First verify if all the views have any data. If there is nothing or amount of data is very limited, generated dummy data for last month and use those instead.

```

Another task related to cost control is assigning credit limits per user. We can do it by following ALTER statements:
```
----setting the limit to protect trial credits
ALTER ACCOUNT SET CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER = 10;

--setting the limit to protect trial credits
ALTER ACCOUNT SET CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER = 10;

```