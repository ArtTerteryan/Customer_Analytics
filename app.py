"""
AI Receptionist Usage Dashboard (Streamlit)

Run with:
    pip install -r requirements.txt
    streamlit run app.py

All agent stat tables are shown on one page. Data is fetched fresh from each
Google Sheet on every page load (no caching).
"""

import calendar
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime

import pandas as pd
import streamlit as st

# --------------------------- CONFIG ---------------------------
SHEETS_TEXT = """
AR00003: https://docs.google.com/spreadsheets/d/1I6kv2OvpnNSdq4ALyWxh1lCvJ53HrKFJ7IwrZZtblK8/edit?usp=sharing
AR00005: https://docs.google.com/spreadsheets/d/1wMyTmbYCZQ2_fxCKW_MKIOLXQNrNMoiaPn0DY5qsm5I/edit?usp=sharing
AR00007: https://docs.google.com/spreadsheets/d/1Y4GGIMTSnrGcprSk0NpOTkhf43ULyPqCIhyVVHhNSak/edit?ouid=101240097193849099161&usp=sheets_home&ths=true
AR00010: https://docs.google.com/spreadsheets/d/1ZIJvGLH2JJE3Dzgy7k_T5Rq6KZvEFLUws4rjQ5coew4/edit?gid=0#gid=0
AR00011: https://docs.google.com/spreadsheets/d/1lAEVTw7cCBORKM06rgRe7oQqQpwfOahq9IXWuBZgS0U/edit?usp=sharing
AR00012: https://docs.google.com/spreadsheets/d/1wbFDNgSbCiM1Oju-cGBE_JwxrGk7zEqzmgGCokQWaFg/edit?usp=sharing
AR00013 Support: https://docs.google.com/spreadsheets/d/1Hxv21V5wx8inlGofql9xNs8uaxkTd5u511bWjML--Zk/edit?usp=sharing
AR00013: https://docs.google.com/spreadsheets/d/1sMcmEHvpkkRf7mFJOOOq3DuscKT8aPwDOy9GyQqAoxs/edit?gid=0#gid=0
AR00015: https://docs.google.com/spreadsheets/d/1zbkf8iV9r2ZZAoSKAsSZh41C50kRXFgVZb3EMj52QLE/edit?usp=sharing
AR00016: https://docs.google.com/spreadsheets/d/1Rx23fqiUImvmITDHItIkp_3EGJM0deJm5-DJ1bT49Dg/edit?usp=sharing
AR00019: https://docs.google.com/spreadsheets/d/1a7u-NcsVtSS1agNF7K9MTEY3k54sTk9hu0j-Fdru07Y/edit?usp=sharing
AR00020: https://docs.google.com/spreadsheets/d/1-1UoU_XNyqL0S9BnFGJsiFobUvWvppqj7d-ZnxxcKz4/edit?usp=sharing
AR00024: https://docs.google.com/spreadsheets/d/1Ckll7Y1zyJngvjQjTwOfR1Amkz5HtgyYWL88i0yOEdo/edit?usp=sharing
AR00026: https://docs.google.com/spreadsheets/d/1aX8mISjh-4DAGP82IABsrtBiojJFFyTaQekguvfavGQ/edit?usp=sharing
AR00028: https://docs.google.com/spreadsheets/d/16wJOdiCuTg0JlIf1qE_nNZgn4QJBBTEvHyOPM3r8Bhc/edit?usp=sharing
AR00029: https://docs.google.com/spreadsheets/d/1CQCQDoTJjxYNlJjuwqpRHeitTUpgnFIE2cxTIGJrA5A/edit?usp=sharing
AR00030: https://docs.google.com/spreadsheets/d/1Gfei9yD_oiPmwHlE5rvWLpFUEupmeBLvqZ6Tz9sfkuc/edit?usp=sharing
AR00031: https://docs.google.com/spreadsheets/d/1Iozd7Aebj5zyAhDA0rLxAq_vW5QNdN-nD7NxrhOCtoY/edit?usp=sharing
AR00033: https://docs.google.com/spreadsheets/d/1DR6fpIF78WNZr9FhNL_GRa2Xc5ZOl0_FNTBAdUI_Ipk/edit?gid=0#gid=0
AR00037: https://docs.google.com/spreadsheets/d/1CEulCtNzC82P6EgqhDNCwmmGNlpOKUJxOlRZpTKoQXQ/edit?gid=0#gid=0
AR00040: https://docs.google.com/spreadsheets/d/1pedJ4y3I89yzqEqIw9qp3t8-G8YFYcdUHNzwIyUeFhM/edit?gid=0#gid=0
AR00041: https://docs.google.com/spreadsheets/d/1s_i96_oFl789kYF2ML1dX1LlWgLWDOG2QQsyMFKnJ1Y/edit?gid=0#gid=0
AR00045: https://docs.google.com/spreadsheets/d/1YrqGTP8kIgyVqcv8kpYlzgpgbW9BUIsJdeFun9UIiPU/edit?gid=0#gid=0
AR00047: https://docs.google.com/spreadsheets/d/1A8IAlMsU8qnctCN3eOft5LvT9bicouFLZ8YUDKHpXNA/edit?gid=0#gid=0
AR00048: https://docs.google.com/spreadsheets/d/1dnbjnUMQGl4gXYYXW56RaTVfqhSQdhzi8OnmVc3n1Dc/edit?gid=0#gid=0
AR00049: https://docs.google.com/spreadsheets/d/1jq5Kxv9CsiPWIO0z5oPmXkKFJxe0E5TCfDPEEjdXxEQ/edit?gid=0#gid=0
AR00050: https://docs.google.com/spreadsheets/d/1XyDcbHs2Kn4Ic66pp4qEj-GS6QJGkTNEFZCLsFmhyFQ/edit?gid=0#gid=0
AR00051: https://docs.google.com/spreadsheets/d/1b-aX52iqn66EjzeAkW9-mXw21umtDMqlrOfFU7EUoao/edit?gid=0#gid=0
""".strip()

DEFAULT_GID = "0"
COL_CALLDATE = "Call Date"
COL_DURATION = "Total Duration (Seconds)"
COL_PRICE = "Price Per Call"  # per-call cost (in cents); preferred source for total cost
COST_PER_MINUTE = 0.22         # fallback rate if COL_PRICE column is missing
COLUMNS_PER_ROW = 3  # how many agent tables to show side-by-side

# Billing day-of-month per agent. The current billing period runs from the
# most recent occurrence of this day (inclusive) to the next occurrence
# (exclusive). For days that don't exist in a given month (e.g. day 31 in
# April or February), the effective billing date clamps to the last day.
# A single key (e.g. "AR00013") covers any name starting with "AR00013_" or
# "AR00013 " (so AR00013_EST, AR00013 Support, etc. inherit it).
BILLING_DAYS = {
    "AR00003": 5,
    "AR00005": 1,
    "AR00007": 10,
    "AR00010": 18,
    "AR00011": 24,
    "AR00012": 25,
    "AR00013": 31,
    "AR00015": 26,
    "AR00016": 5,
    "AR00019": 9,
    "AR00020": 17,
    "AR00024": 3,
    "AR00026": 9,
    "AR00028": 15,
    "AR00029": 16,
    "AR00031": 27,
    "AR00033": 7,
    "AR00037": 22,
    "AR00040": 10,
    "AR00041": 8,
    "AR00045": 12,
    "AR00047": 24,
    "AR00049": 29,
    "AR00050": 29,
    "AR00051": 4
}


def get_billing_day(name: str):
    """Look up an agent's billing day. Exact match first, then prefix match
    where the prefix is followed by ' ' or '_'."""
    if name in BILLING_DAYS:
        return BILLING_DAYS[name]
    for key, day in BILLING_DAYS.items():
        if name.startswith(key + " ") or name.startswith(key + "_"):
            return day
    return None


def get_billing_period(billing_day: int, today: date | None = None):
    """Return (start, end) of the current billing period as date objects.
    Period is [start, end) — start inclusive, end exclusive.
    Days beyond a month's last day clamp to that month's last day."""
    if today is None:
        today = date.today()

    def effective(year: int, month: int, day: int) -> int:
        return min(day, calendar.monthrange(year, month)[1])

    this_month = date(today.year, today.month, effective(today.year, today.month, billing_day))

    if today >= this_month:
        start = this_month
        ny, nm = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
        end = date(ny, nm, effective(ny, nm, billing_day))
    else:
        py, pm = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
        start = date(py, pm, effective(py, pm, billing_day))
        end = this_month

    return start, end

# --------------------------- HELPERS ---------------------------
def extract_sheet_id_and_gid(url: str, default_gid: str = "0"):
    url = url.strip()
    m = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if not m:
        raise ValueError(f"Could not parse sheet_id from URL: {url}")
    sheet_id = m.group(1)
    # Match gid in query (?gid= / &gid=) or fragment (#gid=)
    gid_match = re.search(r"[?&#]gid=(\d+)", url)
    gid = gid_match.group(1) if gid_match else default_gid
    return sheet_id, gid


def sheet_to_csv_url(sheet_id: str, gid: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def parse_sheets_text(text: str):
    """
    Each line is NAME<separator>URL, where separator is any of:
      - whitespace (space, tab)
      - colon + whitespace ("NAME: URL")
    Names may contain spaces (e.g. "AR00013 Support"). The URL is identified
    by being the substring starting at "http". Lines with no URL keep their
    name and surface as an error in the UI.
    """
    rows = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        idx = line.find("http")
        if idx == -1:
            name = line.rstrip(": \t")
            url = ""
        else:
            name = line[:idx].rstrip(": \t")
            url = line[idx:].strip()
        rows.append({"name": name, "url": url})
    return rows


def load_sheet_csv(sheet_url: str) -> pd.DataFrame:
    sheet_id, gid = extract_sheet_id_and_gid(sheet_url, DEFAULT_GID)
    csv_url = sheet_to_csv_url(sheet_id, gid)
    return pd.read_csv(csv_url)


def build_stats(df: pd.DataFrame, period_start: date | None = None,
                period_end: date | None = None):
    """Return (stats_dataframe, projected_period_spend_float)."""
    required = [COL_CALLDATE, COL_DURATION]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")

    df = df.copy()
    df[COL_CALLDATE] = df[COL_CALLDATE].astype(str).str.strip()
    df["call_dt"] = pd.to_datetime(df[COL_CALLDATE], dayfirst=True, errors="coerce")
    df[COL_DURATION] = pd.to_numeric(df[COL_DURATION], errors="coerce")
    df = df.dropna(subset=["call_dt", COL_DURATION])
    df["call_date"] = df["call_dt"].dt.date

    # Filter to billing period [start, end) if one was provided
    if period_start is not None and period_end is not None:
        df = df[(df["call_date"] >= period_start) & (df["call_date"] < period_end)]

    # Determine days_elapsed and period_length for averages/projections
    today = date.today()
    if period_start is not None and period_end is not None:
        period_length = (period_end - period_start).days
        days_elapsed = max(1, min((today - period_start).days + 1, period_length))
    else:
        period_length = max(1, df["call_date"].nunique()) if len(df) else 1
        days_elapsed = period_length

    if len(df) == 0:
        empty = pd.DataFrame(
            [
                ("Total calls", 0),
                ("Total minutes", 0.0),
                ("Avg call length (min)", 0.0),
                ("Total cost ($)", 0.0),
                ("Avg calls/day", 0.0),
                ("Avg spend/day ($)", 0.0),
                (f"Projected period calls ({period_length}d)", 0),
                (f"Projected period spend ({period_length}d) ($)", 0.0),
            ],
            columns=["Metric", "Value"],
        )
        return empty, 0.0, 0

    df["duration_min"] = df[COL_DURATION] / 60.0

    # Cost: prefer the per-call cost column; fall back to minutes * rate.
    # The column is matched case-insensitively (sheets use "Price Per Call").
    # Its values are in CENTS (e.g. 106.07 = $1.06), so divide by 100 for
    # dollars. Strip "$", commas, and whitespace so "$22" or "22 " parse cleanly.
    price_col = next(
        (c for c in df.columns if c.strip().lower() == COL_PRICE.strip().lower()),
        None,
    )
    if price_col is not None:
        cleaned = df[price_col].astype(str).str.replace(r"[$,\s]", "", regex=True)
        df["cost_usd"] = pd.to_numeric(cleaned, errors="coerce").fillna(0.0) / 100.0
    else:
        df["cost_usd"] = df["duration_min"] * COST_PER_MINUTE

    total_calls = int(len(df))
    total_minutes = float(df["duration_min"].sum())
    total_cost = float(df["cost_usd"].sum())
    avg_call_length = float(df["duration_min"].mean())

    avg_calls_per_day = total_calls / days_elapsed
    avg_spend_per_day = total_cost / days_elapsed
    projected_period_spend = avg_spend_per_day * period_length
    projected_period_calls = int(round(avg_calls_per_day * period_length))

    stats = pd.DataFrame(
        [
            ("Total calls", total_calls),
            ("Total minutes", round(total_minutes, 2)),
            ("Avg call length (min)", round(avg_call_length, 2)),
            ("Total cost ($)", round(total_cost, 2)),
            ("Avg calls/day", round(avg_calls_per_day, 2)),
            ("Avg spend/day ($)", round(avg_spend_per_day, 2)),
            (f"Projected period calls ({period_length}d)", projected_period_calls),
            (f"Projected period spend ({period_length}d) ($)", round(projected_period_spend, 2)),
        ],
        columns=["Metric", "Value"],
    )
    return stats, float(projected_period_spend), projected_period_calls


def fetch_one(item: dict) -> dict:
    name = item["name"] or "(unnamed)"
    url = item["url"]

    billing_day = get_billing_day(name)
    if billing_day is not None:
        period_start, period_end = get_billing_period(billing_day)
    else:
        period_start, period_end = None, None

    base = {
        "name": name, "url": url,
        "billing_day": billing_day,
        "period_start": period_start, "period_end": period_end,
    }

    if not url or "docs.google.com/spreadsheets" not in url:
        return {**base, "error": "Missing or invalid URL", "stats": None,
                "projected_spend": None, "projected_calls": None}
    try:
        df = load_sheet_csv(url)
        stats, projected_spend, projected_calls = build_stats(df, period_start, period_end)
        return {**base, "error": None, "stats": stats,
                "projected_spend": projected_spend, "projected_calls": projected_calls}
    except Exception as e:
        return {**base, "error": str(e), "stats": None,
                "projected_spend": None, "projected_calls": None}


# --------------------------- STREAMLIT UI ---------------------------
st.set_page_config(page_title="AI Receptionist Usage", layout="wide")
st.title("AI Receptionist — Usage Report")

top_left, top_right = st.columns([1, 4])
with top_left:
    if st.button("🔄 Refresh"):
        st.rerun()
with top_right:
    st.caption(f"Loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ·  fresh fetch on every visit")

items = parse_sheets_text(SHEETS_TEXT)
if not items:
    st.warning("No agents configured. Edit SHEETS_TEXT in app.py.")
    st.stop()

# Fetch every sheet in parallel
with st.spinner(f"Fetching data for {len(items)} agents…"):
    results = []
    with ThreadPoolExecutor(max_workers=min(8, len(items))) as ex:
        futures = [ex.submit(fetch_one, item) for item in items]
        for fut in as_completed(futures):
            results.append(fut.result())

# Restore original order (parallel fetches return out of order)
order = {item["name"]: i for i, item in enumerate(items)}
results.sort(key=lambda r: order.get(r["name"], 9999))

# Render as a grid
for row_start in range(0, len(results), COLUMNS_PER_ROW):
    cols = st.columns(COLUMNS_PER_ROW)
    for i, result in enumerate(results[row_start:row_start + COLUMNS_PER_ROW]):
        with cols[i]:
            st.subheader(result["name"] or "(unnamed)")

            if result["billing_day"] is not None:
                ps = result["period_start"].strftime("%b %d, %Y")
                pe = result["period_end"].strftime("%b %d, %Y")
                st.caption(f"📅 {ps} → {pe}  ·  day {result['billing_day']}")
            else:
                st.caption("⚠️ No billing day configured — showing all data")

            if result["error"]:
                st.error(result["error"])
                if result["url"]:
                    st.caption(result["url"])
            else:
                st.dataframe(
                    result["stats"],
                    hide_index=True,
                    use_container_width=True,
                )

# --------------------------- GRAND TOTAL ---------------------------
st.markdown("---")

contributing = [r for r in results if r["projected_spend"] is not None]
total_projected_spend = sum(r["projected_spend"] for r in contributing)
total_projected_calls = sum(r["projected_calls"] for r in contributing)
avg_calls_per_day_fleet = total_projected_calls / 30.0
n_total = len(results)
n_ok = len(contributing)

m1, m2 = st.columns(2)
with m1:
    st.metric(
        label="Combined projected period spend",
        value=f"${total_projected_spend:,.2f}",
    )
with m2:
    st.metric(
        label="Avg projected calls per day (fleet)",
        value=f"{avg_calls_per_day_fleet:,.2f}",
        help=f"Sum of projected period calls ({total_projected_calls:,}) ÷ 30",
    )

if n_ok < n_total:
    st.caption(
        f"Computed across **{n_ok} of {n_total}** agents. "
        f"{n_total - n_ok} agent(s) excluded due to fetch errors."
    )
else:
    st.caption(f"Computed across all **{n_total}** agents.")
