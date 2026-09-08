import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
from snowflake.snowpark.context import get_active_session
from datetime import datetime, timedelta
import json

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CREDIT_PRICE_USD = 2.20
INTERFACES = ["CLI", "DESKTOP", "SNOWSIGHT"]
VIEW_MAP = {
    "CLI": "SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY",
    "DESKTOP": "SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_DESKTOP_USAGE_HISTORY",
    "SNOWSIGHT": "SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY",
}
MIN_ROWS_THRESHOLD = 10

st.set_page_config(page_title="CoCo Cost Overview", layout="wide")
session = get_active_session()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def run_query(sql: str) -> pd.DataFrame:
    return session.sql(sql).to_pandas()


def fmt_tokens(v) -> str:
    if pd.isna(v):
        return "0"
    return f"{int(v):,}"


def fmt_credits(v) -> str:
    if pd.isna(v):
        return "0.0000"
    return f"{v:,.4f}"


def fmt_usd(v) -> str:
    if pd.isna(v):
        return "$0.00"
    return f"${v:,.2f}"


# ---------------------------------------------------------------------------
# Data loading — real views first, fallback to dummy
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def check_data_availability() -> dict:
    counts = {}
    for iface, view in VIEW_MAP.items():
        try:
            row = run_query(f"SELECT COUNT(*) AS CNT FROM {view}")
            counts[iface] = int(row["CNT"].iloc[0])
        except Exception:
            counts[iface] = 0
    return counts


@st.cache_data(ttl=300)
def load_real_data(start_date: str, end_date: str) -> pd.DataFrame:
    parts = []
    for iface, view in VIEW_MAP.items():
        sql = f"""
        SELECT
            '{iface}' AS INTERFACE,
            u.USER_ID,
            COALESCE(NULLIF(TRIM(us.FIRST_NAME || ' ' || us.LAST_NAME), ''), us.NAME, u.USER_NAME, 'User ' || u.USER_ID::VARCHAR) AS DISPLAY_NAME,
            COALESCE(us.EMAIL, '') AS EMAIL,
            u.USAGE_TIME,
            u.TOKENS,
            u.TOKEN_CREDITS,
            u.TOKENS_GRANULAR,
            u.CREDITS_GRANULAR
        FROM {view} u
        LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.USERS us
            ON u.USER_ID = us.USER_ID AND us.DELETED_ON IS NULL
        WHERE u.USAGE_TIME >= '{start_date}'::TIMESTAMP_NTZ
          AND u.USAGE_TIME < '{end_date}'::TIMESTAMP_NTZ
        """
        try:
            df = run_query(sql)
            if not df.empty:
                parts.append(df)
        except Exception:
            pass
    if parts:
        return pd.concat(parts, ignore_index=True)
    return pd.DataFrame()


def generate_dummy_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    users = [
        (1, "Alice Johnson", "alice@example.com"),
        (2, "Bob Smith", "bob@example.com"),
        (3, "Carlos Garcia", "carlos@example.com"),
        (4, "Diana Lee", "diana@example.com"),
        (5, "Erik Muller", "erik@example.com"),
        (6, "Fatima Hassan", "fatima@example.com"),
        (7, "Grace Kim", "grace@example.com"),
        (8, "Henrik Larsen", "henrik@example.com"),
    ]
    models = ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5"]
    model_credit_rates = {"claude-opus-4-6": 0.0010, "claude-sonnet-4-6": 0.00030, "claude-haiku-4-5": 0.00015}
    rows = []
    end = datetime.now()
    start = end - timedelta(days=30)
    for day_offset in range(30):
        dt = start + timedelta(days=day_offset)
        for uid, name, email in users:
            for iface in INTERFACES:
                weight = {"CLI": 0.6, "DESKTOP": 0.5, "SNOWSIGHT": 0.4}[iface]
                n_requests = rng.poisson(lam=12 * weight)
                for _ in range(n_requests):
                    model = rng.choice(models, p=[0.3, 0.5, 0.2])
                    tokens = int(rng.lognormal(mean=10, sigma=1))
                    credits = tokens * model_credit_rates[model]
                    granular_t = json.dumps({model: {"input": int(tokens * 0.7), "output": int(tokens * 0.3)}})
                    granular_c = json.dumps({model: round(credits, 6)})
                    hour = rng.integers(8, 20)
                    minute = rng.integers(0, 60)
                    ts = dt.replace(hour=hour, minute=minute, second=0)
                    rows.append({
                        "INTERFACE": iface,
                        "USER_ID": uid,
                        "DISPLAY_NAME": name,
                        "EMAIL": email,
                        "USAGE_TIME": ts,
                        "TOKENS": tokens,
                        "TOKEN_CREDITS": credits,
                        "TOKENS_GRANULAR": granular_t,
                        "CREDITS_GRANULAR": granular_c,
                    })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("Filters")

availability = check_data_availability()
total_real = sum(availability.values())
using_dummy = total_real < MIN_ROWS_THRESHOLD

if using_dummy:
    st.sidebar.warning(f"Live data has only {total_real} rows. Showing **dummy data** for demo purposes.")
else:
    st.sidebar.success(f"Live data: {total_real:,} total rows across all interfaces.")

period = st.sidebar.selectbox("Time Period", ["Last 30 Days", "Last 7 Days", "Last Day", "Custom"])
now = datetime.now()
if period == "Last Day":
    start_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
elif period == "Last 7 Days":
    start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
elif period == "Last 30 Days":
    start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
else:
    col1, col2 = st.sidebar.columns(2)
    d1 = col1.date_input("Start", value=now - timedelta(days=30))
    d2 = col2.date_input("End", value=now)
    start_date = d1.strftime("%Y-%m-%d")
    end_date = (d2 + timedelta(days=1)).strftime("%Y-%m-%d")

if using_dummy:
    raw = generate_dummy_data()
    raw["USAGE_TIME"] = pd.to_datetime(raw["USAGE_TIME"])
    mask = (raw["USAGE_TIME"] >= start_date) & (raw["USAGE_TIME"] < end_date)
    data = raw[mask].copy()
else:
    data = load_real_data(start_date, end_date)
    if not data.empty:
        data["USAGE_TIME"] = pd.to_datetime(data["USAGE_TIME"])

if data.empty:
    st.title("CoCo Cost Overview")
    st.info("No usage data found for the selected period. These views lag 45 min – 2 hours behind real time.")
    st.stop()

all_users = sorted(data["DISPLAY_NAME"].unique().tolist())
selected_users = st.sidebar.multiselect("Users", all_users, default=all_users)
if selected_users:
    data = data[data["DISPLAY_NAME"].isin(selected_users)]

if data.empty:
    st.title("CoCo Cost Overview")
    st.info("No data after applying user filter.")
    st.stop()

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
st.title("CoCo Cost Overview")
if using_dummy:
    st.caption("Showing generated dummy data — live views have insufficient rows.")

# ---------------------------------------------------------------------------
# Per-interface metric rows + combined total
# ---------------------------------------------------------------------------
st.subheader("Usage Summary")

metrics = []
for iface in INTERFACES:
    subset = data[data["INTERFACE"] == iface]
    tokens = subset["TOKENS"].sum()
    credits = subset["TOKEN_CREDITS"].sum()
    cost = credits * CREDIT_PRICE_USD
    metrics.append({"Interface": iface, "Tokens": tokens, "Credits": credits, "Cost (USD)": cost})

total_tokens = sum(m["Tokens"] for m in metrics)
total_credits = sum(m["Credits"] for m in metrics)
total_cost = sum(m["Cost (USD)"] for m in metrics)
metrics.append({"Interface": "TOTAL", "Tokens": total_tokens, "Credits": total_credits, "Cost (USD)": total_cost})

cols = st.columns(4)
for i, m in enumerate(metrics):
    with cols[i]:
        label = m["Interface"]
        st.metric(f"{label} Tokens", fmt_tokens(m["Tokens"]))
        st.metric(f"{label} Credits", fmt_credits(m["Credits"]))
        st.metric(f"{label} Cost", fmt_usd(m["Cost (USD)"]))

# ---------------------------------------------------------------------------
# Token consumption over time — one line chart per interface
# ---------------------------------------------------------------------------
st.subheader("Token Consumption Over Time (Daily)")

data["DATE"] = data["USAGE_TIME"].dt.date
daily = data.groupby(["DATE", "INTERFACE"], as_index=False).agg(TOKENS=("TOKENS", "sum"))
daily["DATE"] = pd.to_datetime(daily["DATE"])

chart_cols = st.columns(3)
for i, iface in enumerate(INTERFACES):
    with chart_cols[i]:
        st.markdown(f"**{iface}**")
        iface_daily = daily[daily["INTERFACE"] == iface]
        if iface_daily.empty:
            st.info(f"No {iface} data in this period.")
        else:
            chart = (
                alt.Chart(iface_daily)
                .mark_line(point=True)
                .encode(
                    x=alt.X("DATE:T", title="Date"),
                    y=alt.Y("TOKENS:Q", title="Tokens", axis=alt.Axis(format=",")),
                    tooltip=[
                        alt.Tooltip("DATE:T", title="Date"),
                        alt.Tooltip("TOKENS:Q", title="Tokens", format=","),
                    ],
                )
                .properties(height=300)
                .interactive()
            )
            st.altair_chart(chart, use_container_width=True)

# ---------------------------------------------------------------------------
# Cost by model
# ---------------------------------------------------------------------------
st.subheader("Cost by Model")


def flatten_credits_granular(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        raw = row["CREDITS_GRANULAR"]
        if pd.isna(raw) or raw is None:
            continue
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
        else:
            parsed = raw
        if isinstance(parsed, dict):
            for model, val in parsed.items():
                if isinstance(val, dict):
                    credit_val = sum(v for v in val.values() if isinstance(v, (int, float)))
                else:
                    credit_val = float(val) if val else 0
                rows.append({"MODEL": model, "CREDITS": credit_val})
    return pd.DataFrame(rows)


model_df = flatten_credits_granular(data)

if model_df.empty:
    st.info("No per-model granular data available.")
else:
    model_agg = model_df.groupby("MODEL", as_index=False).agg(CREDITS=("CREDITS", "sum"))
    model_agg["COST_USD"] = model_agg["CREDITS"] * CREDIT_PRICE_USD
    model_agg = model_agg.sort_values("COST_USD", ascending=False)

    col_chart, col_table = st.columns([2, 1])
    with col_chart:
        bar = (
            alt.Chart(model_agg)
            .mark_bar()
            .encode(
                x=alt.X("MODEL:N", title="Model", sort="-y"),
                y=alt.Y("COST_USD:Q", title="Cost (USD)", axis=alt.Axis(format="$,.2f")),
                color=alt.Color("MODEL:N", legend=None),
                tooltip=[
                    alt.Tooltip("MODEL:N", title="Model"),
                    alt.Tooltip("CREDITS:Q", title="Credits", format=",.4f"),
                    alt.Tooltip("COST_USD:Q", title="Cost (USD)", format="$,.2f"),
                ],
            )
            .properties(height=350)
            .interactive()
        )
        st.altair_chart(bar, use_container_width=True)
    with col_table:
        display_model = model_agg.copy()
        display_model["CREDITS"] = display_model["CREDITS"].apply(fmt_credits)
        display_model["COST_USD"] = display_model["COST_USD"].apply(fmt_usd)
        display_model.columns = ["Model", "Credits", "Cost (USD)"]
        st.dataframe(display_model, use_container_width=True)

# ---------------------------------------------------------------------------
# Per-user table
# ---------------------------------------------------------------------------
st.subheader("Per-User Breakdown")

user_rows = []
for (uid, name, email), grp in data.groupby(["USER_ID", "DISPLAY_NAME", "EMAIL"]):
    row = {"User": name, "Email": email}
    total_tok = 0
    total_cred = 0.0
    for iface in INTERFACES:
        sub = grp[grp["INTERFACE"] == iface]
        tok = sub["TOKENS"].sum()
        cred = sub["TOKEN_CREDITS"].sum()
        row[f"{iface} Tokens"] = tok
        row[f"{iface} Credits"] = cred
        total_tok += tok
        total_cred += cred
    row["Total Tokens"] = total_tok
    row["Total Credits"] = total_cred
    row["Total Cost (USD)"] = total_cred * CREDIT_PRICE_USD
    user_rows.append(row)

user_df = pd.DataFrame(user_rows).sort_values("Total Cost (USD)", ascending=False).reset_index(drop=True)

PAGE_SIZE = 20
if "user_table_rows" not in st.session_state:
    st.session_state.user_table_rows = PAGE_SIZE

show_n = min(st.session_state.user_table_rows, len(user_df))
display_df = user_df.head(show_n).copy()

format_cols = {
    "Total Cost (USD)": fmt_usd,
    "Total Credits": fmt_credits,
    "Total Tokens": fmt_tokens,
}
for iface in INTERFACES:
    format_cols[f"{iface} Tokens"] = fmt_tokens
    format_cols[f"{iface} Credits"] = fmt_credits

for col, fn in format_cols.items():
    if col in display_df.columns:
        display_df[col] = display_df[col].apply(fn)

st.dataframe(display_df, use_container_width=True)

if show_n < len(user_df):
    if st.button(f"Show More ({len(user_df) - show_n} remaining)"):
        st.session_state.user_table_rows += PAGE_SIZE
        st.rerun()

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(f"Credit price: ${CREDIT_PRICE_USD:.2f}/credit · Data source: SNOWFLAKE.ACCOUNT_USAGE · "
           f"Views lag 45 min – 2 hours behind real time")
