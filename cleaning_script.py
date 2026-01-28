import pandas as pd
from pathlib import Path
import webbrowser

# ================= CONFIG =================
DATA_PATH = Path("/Users/homesachin/Downloads")
OUTPUT_HTML = "email_deliverability_report.html"

COL_EMAIL = "email#"
COL_HAS_LOGGED_IN = "has_logged_in$"

BUCKET_EXPLAINERS = {
    "A": "Active users; stop bulk emails, allow transactional messages only",
    "B": "Spam reporters; permanently block all emails, keep account",
    "C": "Hard bounce, no login; mark inactive and review later",
    "D": "Obvious junk emails; safe to archive or soft delete",
    "E": "Temporary delivery issues; pause emails and retry later",
}

# ================= HELPERS =================
def normalize_email(email):
    if pd.isna(email):
        return None
    return email.strip().lower()

def severity_from_reason(reason):
    if not isinstance(reason, str):
        return "low"
    r = reason.lower()
    if r.startswith("550") or "does not exist" in r:
        return "high"
    if "spam" in r:
        return "critical"
    return "low"

def determine_bucket(row):
    stype = row["suppression_type$"]
    logged_in = row[COL_HAS_LOGGED_IN]

    if stype == "spam":
        return "A" if logged_in else "B"
    if stype == "invalid":
        return "D"
    if stype == "bounce":
        return "C" if not logged_in else "A"
    return "E"

# ================= LOAD CSVs =================
blocks_df = pd.read_csv(DATA_PATH / "suppression_blocks.csv")
bounces_df = pd.read_csv(DATA_PATH / "suppression_bounces.csv")
invalid_df = pd.read_csv(DATA_PATH / "suppression_invalid_emails.csv")
spam_df = pd.read_csv(DATA_PATH / "suppression_spam_reports.csv")

for df in [blocks_df, bounces_df, invalid_df, spam_df]:
    df["email"] = df["email"].apply(normalize_email)

# ================= BUILD SUPPRESSION MASTER =================
def build_frame(df, stype):
    temp = df[["email"]].copy()
    temp["suppression_type$"] = stype
    temp["suppression_code_reason#"] = df["reason"] if "reason" in df.columns else ""
    return temp

suppression_df = pd.concat([
    build_frame(blocks_df, "block"),
    build_frame(bounces_df, "bounce"),
    build_frame(invalid_df, "invalid"),
    build_frame(spam_df, "spam"),
]).drop_duplicates("email")

# ================= SIMULATED USER DATA =================
suppression_df["user_id#"] = ["U" + str(1000 + i) for i in range(len(suppression_df))]
suppression_df["user_role#"] = ["investor"] * len(suppression_df)
suppression_df["last_login#"] = pd.NaT
suppression_df[COL_HAS_LOGGED_IN] = False
suppression_df["login_allowed#"] = True

# ================= DERIVED COLUMNS =================
suppression_df["severity$"] = suppression_df["suppression_code_reason#"].apply(severity_from_reason)
suppression_df["bucket$"] = suppression_df.apply(determine_bucket, axis=1)
suppression_df["email_allowed$"] = suppression_df["suppression_type$"].apply(
    lambda x: "fully_blocked" if x in ["spam", "invalid"] else "marketing_disabled"
)
suppression_df["cleanup_candidate$"] = suppression_df["bucket$"].isin(["C", "D"])
suppression_df["suppression_source$"] = "sendgrid"

suppression_df["recommended_action$"] = suppression_df["bucket$"].map({
    "A": "Stop bulk emails, allow transactional",
    "B": "Block all emails, retain account",
    "C": "Mark inactive, review later",
    "D": "Safe soft delete / archive",
    "E": "Retry after cooldown"
})

# ================= FINAL TABLE =================
final_df = suppression_df[[
    "bucket$",
    "email",
    "user_id#",
    "user_role#",
    COL_HAS_LOGGED_IN,
    "last_login#",
    "suppression_source$",
    "suppression_type$",
    "suppression_code_reason#",
    "severity$",
    "email_allowed$",
    "login_allowed#",
    "cleanup_candidate$",
    "recommended_action$"
]].rename(columns={"email": COL_EMAIL})

final_df["last_login#"] = final_df["last_login#"].fillna(
    "No login timestamp exists for the user"
)

# ================= BUCKET COUNTS =================
bucket_counts = final_df["bucket$"].value_counts().to_dict()
safe_cleanup_count = bucket_counts.get("D", 0)

# ================= HTML OUTPUT =================
html = f"""
<!DOCTYPE html>
<html>
<head>
<title>Email Deliverability Audit Report</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body {{ padding:30px; background:#f4f6f8; }}

.badge-A {{ background:#198754; }}
.badge-B {{ background:#0d6efd; }}
.badge-C {{ background:#fd7e14; }}
.badge-D {{ background:#dc3545; }}
.badge-E {{ background:#6c757d; }}

th.hash {{ background:#198754 !important; color:white; }}
th.dollar {{ background:#8b5a2b !important; color:white; }}

table {{ background:white; font-size:14px; }}
th {{ position:sticky; top:0; }}
</style>
</head>
<body>

<h2>Email Deliverability Audit Report</h2>

<div class="row mb-4">
{''.join([
    f"""
    <div class="col">
        <div class="card text-center h-100">
            <div class="card-body">
                <span class="badge badge-{k}">Bucket {k}</span>
                <h4 class="mt-2">{bucket_counts.get(k, 0)}</h4>
                <p class="text-muted small mt-2">
                    {BUCKET_EXPLAINERS[k]}
                </p>
            </div>
        </div>
    </div>
    """
    for k in ["A", "B", "C", "D", "E"]
])}
</div>

<div class="alert alert-success mb-4">
    <strong>Safe Cleanup Summary:</strong>
    Based on the latest cron run and current data,
    <strong>{safe_cleanup_count}</strong> email records
    are safe to archive or soft delete with no user or business impact.
</div>

<table class="table table-bordered table-hover">
<thead>
<tr>
{''.join([
    f"<th class='{'hash' if c.endswith('#') else 'dollar' if c.endswith('$') else ''}'>{c}</th>"
    for c in final_df.columns
])}
</tr>
</thead>
<tbody>
"""

for _, row in final_df.iterrows():
    html += "<tr>"
    for col in final_df.columns:
        if col == "bucket$":
            html += f"<td><span class='badge badge-{row[col]}'>{row[col]}</span></td>"
        else:
            html += f"<td>{row[col]}</td>"
    html += "</tr>"

html += """
</tbody>
</table>
</body>
</html>
"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

webbrowser.open(f"file://{Path(OUTPUT_HTML).resolve()}")

print("✅ Report generated and opened in browser")
