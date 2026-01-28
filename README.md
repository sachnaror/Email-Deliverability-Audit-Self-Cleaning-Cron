# 📧 Email Deliverability Audit & Self-Cleaning System

A safe, automated way to improve email deliverability without deleting real users,
investors, or compliance-relevant records.

---

## 🧩 Problem Statement

Over time, systems accumulate bounced, invalid, and spam-reported email addresses.
Blind deletion is risky because some emails belong to real users or investors, while
not cleaning them hurts sender reputation and email deliverability.

Manual cleanup does not scale and is error-prone.

---

## 🎯 What This Project Does

This project introduces a **rule-based email audit system** that:

- Separates **email behaviour** from **user identity**
- Preserves all user accounts by default
- Identifies only **high-confidence junk** for cleanup
- Improves email deliverability automatically
- Can run every 30–60 days with zero manual effort

---

## 🧠 Core Principle

> We do not delete people.  
> We control communication first and archive only clearly dead records.

---

## 📥 Input Data

The script consumes CSV exports from SendGrid and internal systems:

- `suppression_blocks.csv`
- `suppression_bounces.csv`
- `suppression_invalid_emails.csv`
- `suppression_spam_reports.csv`

All files are read in read-only mode from a single directory.

---

## 🧺 Bucket Classification (A–E)

| Bucket | Meaning |
|------|--------|
| A | Active users with email delivery issues |
| B | Spam reporters |
| C | Never logged in + hard bounce |
| D | Obvious junk / test emails |
| E | Temporary delivery issues |

---

## 🧾 Action Policy (Final)

- **Bucket A**: Stop bulk emails, allow transactional only  
- **Bucket B**: Block all emails permanently, keep account  
- **Bucket C**: Mark inactive, stop emails, reactivate only after login + valid email  
- **Bucket D**: Safe to archive or soft delete (only cleanup bucket)  
- **Bucket E**: Pause emails for 30–60 days and retry later  

---

## 🧪 Output

- Human-readable **HTML audit report**
- Bucket-wise counts and explanations
- Clear **Safe Cleanup Summary** (Bucket D only)
- Full audit table with color-coded headers
- No technical values like `NaT` (plain English instead)

---

## 🔁 Automation

Designed to run as a **cron job**:

- Frequency: every 30 or 60 days
- Fully self-cleaning over time
- No manual intervention needed

Example:
```bash
0 2 1 * * python email_deliverability_report.py
```

---

## 🏗 Architecture Snapshot

Replace the image below with a real diagram or screenshot.

![Email Deliverability Architecture](email_architecture_diagram.png)

---

## ⚙️ Requirements & Run

```bash
python -m pip install pandas
python email_deliverability_report.py
```

The HTML report opens automatically in the browser.

---

## 📩 Contact

| Name              | Details                             |
|-------------------|-------------------------------------|
| **👨‍💻 Developer** | Sachin Arora |
| **📧 Email** | sachnaror@gmail.com |
| **📍 Location** | Noida, India |
| **📂 GitHub** | https://github.com/sachinaror |
| **🌐 Website** | https://about.me/sachin-arora |
| **📱 Phone** | +91 9560330483 |

Happy coding! 🎯🔥
