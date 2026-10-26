# Retail Sales Case Study: Who Drives Revenue, and Who Are We Losing?

**Business question:** A UK online gift retailer wants to know where its revenue really comes from, which customers matter most, and what to do next.

**Short answer:** About **26% of customers ("Champions") generate 67% of revenue**, November sales run **2.4x the spring average**, and **65% of customers buy more than once**, but 273 formerly frequent buyers have gone quiet and are worth a win-back campaign.

**Data:** [UCI Online Retail dataset](https://archive.ics.uci.edu/dataset/352/online+retail) (real transactions, 1 Dec 2010 to 9 Dec 2011, about 540,000 rows, CC BY 4.0). It is real, messy data, so cleaning is part of the work.

## Key findings
| # | Finding | Evidence |
|---|---|---|
| 1 | Revenue is concentrated in loyal customers | Champions (high recency and frequency) are 26% of customers and 67% of revenue. The top 20% of customers by spend account for 75%. |
| 2 | Strong seasonality | November 2011 revenue was about £1.45M versus about £0.61M average for Feb to May. Plan stock and cash for Sep to Nov. |
| 3 | Good repeat behavior, bursty timing | 65% of customers ordered more than once. About 21% of a monthly cohort buys again the next month, and 25% three months later. |
| 4 | A win-back opportunity | 273 customers (6% of customers, 5% of revenue) were frequent buyers but have not purchased recently. |
| 5 | The UK is the market | The UK is 85% of revenue. The top non-UK markets are the Netherlands, Ireland, Germany, France and Australia. |
| 6 | Returns and data capture need attention | About 15% of invoices are cancellations or returns, worth about £0.9M (9% of clean revenue). 25% of rows (15% of revenue) have no customer ID, so they can't be linked to a customer. |

![Monthly revenue](figures/monthly_revenue.png)
![Revenue concentration](figures/revenue_concentration.png)
![RFM segments](figures/rfm_segments.png)
![Cohort retention](figures/cohort_retention.png)

## Recommendations
1. **Protect the Champions.** Give early access, wholesale pricing or loyalty perks. Losing a few of them costs more than losing many small buyers.
2. **Run a win-back campaign** for the 273 "at risk" customers, since they have a proven buying history.
3. **Prepare for the Sep to Nov peak:** stock, staffing and cash flow.
4. **Capture customer ID at checkout** (including guest buyers) so a quarter of the data isn't wasted.
5. **Investigate cancellations**: find which products and periods drive them.

## Method
1. **Clean** (counts in `results/cleaning_log.csv`): removed cancellation invoices, non-product codes (postage, fees, manual entries), zero or negative quantities and prices, and exact duplicates. This left about 522,500 rows and £10.2M of revenue.
2. **Revenue analysis:** monthly trend and country split.
3. **RFM segmentation:** recency, frequency and monetary value scored in quintiles for the 4,334 identified customers, then grouped into segments.
4. **Cohort retention:** customers grouped by first purchase month and tracked over time.

## Limitations (read these before drawing conclusions)
- One retailer, about 12 months of data. Seasonality is based on a single year.
- December 2011 is a partial month (data ends 9 Dec) and is excluded from retention averages.
- Cancellations are not matched back to the original sale, so returns by product aren't measured.
- Segment cut-offs are quintile-based choices, not the only valid ones.
- Customer-level numbers cover only rows that have a customer ID.

## Reproduce
```bash
pip install -r requirements.txt
python download_data.py    # downloads the dataset (about 45 MB)
python analysis.py         # builds figures/ and results/
```

## Files
`analysis.py` (all the code), `results/` (CSV tables and `summary.json`), `figures/` (charts).

*Dataset: Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository.*
