---
name: site-users-count
description: "Query and analyze online user count data from the wireless database's online_users_count table. Use this skill whenever the user asks about site-level user counts, online user statistics, network device counts (NAC/controller), or any question involving site_code/site_name, user numbers, and dates. This includes: looking up a specific site's user count on a given day, viewing trends over a date range, comparing multiple sites, aggregating by site_owner/priority/business, exporting reports to Excel, or generating charts (line/bar/pie). Also trigger when the user mentions '人数', '在线人数', '站点人数', 'site users', 'online users', 'user count', '无线网络人数', or wants any statistical summary from the online_users_count table — even if they don't explicitly say 'database' or 'query'. The skill is read-only: it never modifies data."
---

# Site Online Users Count Query Skill

This skill queries the `online_users_count` table in the `wireless` database to retrieve and analyze site-level user count data. It supports flexible querying, aggregation, Excel export, and chart generation.

## Database Connection

The script reads credentials from a `.env` file in the project root. The expected variables:

```
DB_HOST=<host>
DB_PORT=5432
DB_USER=<user>
DB_PASSWORD=<password>
DB_NAME=wireless
```

If the `.env` file is elsewhere, pass `--env-path /path/to/.env` to the script.

## Table Structure: `online_users_count`

| Field | Type | Description |
|---|---|---|
| `site_code` | varchar(255) | Unique site identifier |
| `site_name` | varchar(255) | Human-readable site name |
| `count` | int | Total online user count |
| `count_nac` | int | NAC (Network Access Control) user count |
| `count_controller` | int | Wireless controller user count |
| `site_owner` | varchar(255) | Person or team responsible for the site |
| `site_function` | varchar(255) | Functional category of the site |
| `priority` | varchar(64) | Priority level (e.g., High/Medium/Low) |
| `business` | varchar(255) | Business unit or department |
| `create_time` | datetime | Record creation timestamp |
| `update_time` | datetime | Record last updated timestamp |

## Critical Safety Constraint

This skill is strictly **read-only**. The bundled script (`scripts/query_db.py`) enforces this at multiple layers:
1. **Connection-level**: Opens the PostgreSQL session in read-only mode via `conn.set_session(readonly=True)` — even if a write query somehow passes validation, PostgreSQL itself will reject it
2. **SQL validation**: Rejects any SQL containing INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, COPY, VACUUM, or other modification keywords
3. **Statement-level**: Only executes statements that start with SELECT, SHOW, DESCRIBE, or EXPLAIN

When writing custom Python scripts that query the database, always import and use the validation functions from `scripts/query_db.py` to maintain the read-only guarantee.

## How to Use

The primary tool is `scripts/query_db.py`. The script path is relative to this skill directory: `.opencode/skills/site-users-count/scripts/query_db.py`

### Query Modes

**1. Query a specific site on a specific date:**
```bash
python scripts/query_db.py --site-code "HQ-BJ-001" --date 2024-01-15
```

**2. Query a site over a date range:**
```bash
python scripts/query_db.py --site-code "HQ-BJ-001" --start-date 2024-01-01 --end-date 2024-01-31
```

**3. Fuzzy search by site name:**
```bash
python scripts/query_db.py --site-name "Beijing" --date 2024-01-15
```

**4. List all distinct sites:**
```bash
python scripts/query_db.py --list-sites
```

**5. Aggregate by a field (e.g., by site_owner):**
```bash
python scripts/query_db.py --group-by site_owner --start-date 2024-01-01 --end-date 2024-01-31
```

Valid `--group-by` values: `site_code`, `site_name`, `site_owner`, `site_function`, `priority`, `business`, `create_time::date`, `EXTRACT(YEAR FROM create_time)`, `EXTRACT(MONTH FROM create_time)`, `TO_CHAR(create_time, 'IYYY-IW')`

**6. Compare multiple sites:**
```bash
python scripts/query_db.py --compare-sites HQ-BJ-001 HQ-SH-002 --start-date 2024-01-01 --end-date 2024-01-31
```

**7. Custom SELECT query:**
```bash
python scripts/query_db.py --sql "SELECT site_name, AVG(count) as avg_count FROM online_users_count WHERE DATE(create_time) = '2024-01-15' GROUP BY site_name ORDER BY avg_count DESC LIMIT 10"
```

### Output Formats

Add `--output <format>` to any query:

| Format | Flag | Description |
|---|---|---|
| Table | `--output table` | Default. ASCII table printed to stdout |
| JSON | `--output json` | JSON array of objects |
| CSV | `--output csv` | CSV file (use `--output-path` to set path) |
| Excel | `--output excel` | Formatted .xlsx file with headers and styling |
| Chart | `--output chart` | PNG chart image |

### Chart Options

When using `--output chart`:

```bash
# Bar chart of daily totals
python scripts/query_db.py --group-by "create_time::date" --start-date 2024-01-01 --end-date 2024-01-31 --output chart --chart-type bar

# Line chart trend for a site
python scripts/query_db.py --site-code "HQ-BJ-001" --start-date 2024-01-01 --end-date 2024-01-31 --output chart --chart-type line --chart-x record_date --chart-y count

# Multi-line comparison of sites
python scripts/query_db.py --compare-sites HQ-BJ-001 HQ-SH-002 HQ-GZ-003 --start-date 2024-01-01 --end-date 2024-01-31 --output chart --chart-type multi_line --chart-x record_date --chart-y count --chart-label site_code
```

Chart types: `bar`, `line`, `pie`, `multi_line`

## Response Rules

Follow these rules to decide how to respond, based on the number of sites and the date range the user is asking about.

### Scenario A: Single site, single day

When the user asks about **one site on one specific date**, just query the data and respond directly with a concise summary. No need to generate Excel or charts.

Example prompts: "SA Riyadh Office 今天多少人", "查一下 BJ-HQ-001 在 2026-04-15 的人数"

Response approach:
1. Run the query
2. Reply with a brief text summary containing count, count_nac, count_controller values

### Scenario B: Single site, multiple days

When the user asks about **one site over a date range** (e.g., "last 7 days", "this month", "2026-04-01 to 2026-04-15"), always do both of the following:

1. **Generate an Excel file** containing all the queried records with proper formatting (use `--output excel` or the `to_excel` function)
2. **Generate a line chart** with three lines: `count`, `count_nac`, `count_controller` over the date range. Write a custom matplotlib script using `from query_db import get_connection, query_by_site_and_date` — this gives more control over the multi-line chart than the built-in `--output chart` mode

The Excel and chart files should be saved to the project root directory with descriptive names (e.g., `<site_name>_<date_range>.xlsx` and `<site_name>_<date_range>_chart.png`).

Example prompts: "SA Riyadh Office 最近一周的人数", "帮我看看北京站点上个月的人数变化"

Response approach:
1. Run the query
2. Save Excel and chart
3. Reply with a brief summary of the data trend, and tell the user where the files are saved

### Scenario C: Multiple sites

When the user asks about **multiple sites** but does not specify exactly which ones, do NOT immediately query all sites. Instead:

1. **Ask the user first**: list available sites (or a relevant subset) and let the user pick which ones they care about. For example, if they say "帮我看看北京几个站点的情况", query distinct sites matching "北京" and present the list for the user to choose from.
2. Once the user confirms the target sites, follow Scenario B's approach: generate both Excel and chart for the selected sites.

If the user already specified exact sites (e.g., "对比 SARUH03 和 BJHQ01"), skip the confirmation step and go directly to generating Excel and chart.

For multi-site charts, use different colors/lines for each site, and include a legend to distinguish them.

Example prompts requiring confirmation: "帮我对比几个站点的人数", "看看priority为P1的站点"
Example prompts not requiring confirmation: "对比 SARUH03 和 BJHQ01 最近一周的人数"

### General rules for all scenarios

- Always determine relative dates from natural language: "今天" → today, "昨天" → yesterday, "上周" → last Mon-Sun, "最近N天" → N days ago to today, "本月" → 1st of month to today
- Use `$(date -d '...' +%Y-%m-%d)` on Linux for shell date arithmetic
- After generating files, tell the user the file paths
- Provide a brief text summary of key findings alongside any generated files
- If the user asks for something that doesn't fit these three scenarios (e.g., aggregation, ranking, ad-hoc analysis), use your judgment to pick the most helpful output format

## Handling User Requests — Step by Step

When a user asks about site user counts, follow these steps:

### Step 1: Classify the request

Determine which scenario applies:
- **Scenario A**: one site, one day → direct answer
- **Scenario B**: one site, multiple days → Excel + chart
- **Scenario C**: multiple sites (unspecified) → ask which sites first, then Excel + chart

Also identify:
- Which site(s)? (site_code or site_name)
- What time period? (a single date, a range, or relative like "last week")

If the user doesn't specify a site or date, start by listing available sites so they can pick:
```bash
python3 scripts/query_db.py --list-sites --output table
```

### Step 2: Determine relative dates

Users often say "today", "yesterday", "last week", "last month", "this week", etc. Convert these:
- "today" / "今天" → `--date $(date +%Y-%m-%d)` or `--start-date` and `--end-date` with the same value
- "yesterday" / "昨天" → compute the date
- "last week" / "上周" → compute start and end of last week
- "last month" / "上个月" → compute start and end of last month
- "last 7 days" / "最近7天" → `--start-date` as 7 days ago, `--end-date` as today
- "last 30 days" / "最近30天" → similar

Use shell arithmetic: `$(date -d '7 days ago' +%Y-%m-%d)` on Linux.

### Step 3: Run the query and generate output

Follow the response rules for the matching scenario.

### Step 4: Summarize

Provide a brief summary of the results:
- What the data shows
- Any notable patterns (e.g., weekday vs weekend differences, peaks, trends)
- Where generated files are saved

## Writing Custom Analysis Scripts

For complex analysis that the CLI doesn't cover, write a Python script that imports from `query_db.py`:

```python
import sys
sys.path.insert(0, '.opencode/skills/site-users-count/scripts')
from query_db import get_connection, execute_query, to_excel, to_chart

conn = get_connection()

# Safe custom query - execute_query validates read-only constraint
data = execute_query(conn, """
    SELECT site_name,
           COUNT(*) as days_recorded,
           AVG(count) as avg_users,
           MAX(count) as peak_users,
           MIN(count) as min_users
    FROM online_users_count
    WHERE DATE(create_time) >= '2024-01-01'
      AND DATE(create_time) <= '2024-01-31'
    GROUP BY site_name
    HAVING avg_users > 100
    ORDER BY avg_users DESC
""")

to_excel(data, 'site_summary_january.xlsx', title='January Site Summary')
conn.close()
```

The `execute_query` function will reject any non-SELECT statement, so there's no risk of accidentally modifying data.

## Common Scenarios

**"帮我看看北京站点最近一周的人数变化"** (Show me Beijing site's user count change over the last week):
```bash
python scripts/query_db.py --site-name "北京" --start-date $(date -d '7 days ago' +%Y-%m-%d) --end-date $(date +%Y-%m-%d) --output chart --chart-type line --chart-x record_date --chart-y count --chart-title "北京站点最近一周在线人数趋势"
```

**"导出所有站点今天的人数到Excel"** (Export all sites' user counts today to Excel):
```bash
python scripts/query_db.py --date $(date +%Y-%m-%d) --output excel --output-path "all_sites_today.xlsx"
```

**"哪个站点人数最多"** (Which site has the most users):
```bash
python scripts/query_db.py --sql "SELECT site_code, site_name, count, count_nac, count_controller FROM online_users_count WHERE create_time::date = CURRENT_DATE ORDER BY count DESC LIMIT 1"
```

**"按site_owner统计总人数"** (Summarize total users by site_owner):
```bash
python scripts/query_db.py --group-by site_owner --start-date $(date +%Y-%m-01) --end-date $(date +%Y-%m-%d) --output chart --chart-type bar --chart-title "各负责人站点总人数"
```

## Dependencies

- Python 3.8+
- `psycopg2` - PostgreSQL database connector
- `python-dotenv` - Read .env files
- `openpyxl` - Excel file generation
- `pandas` - Data manipulation (already available)
- `matplotlib` - Chart generation
