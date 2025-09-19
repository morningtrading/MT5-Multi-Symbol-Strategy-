import json

# Load the data quality report
with open('CSVdata/data_quality_report.json', 'r') as f:
    data = json.load(f)

xrp = data['symbol_reports']['XRPUSD']

print('XRPUSD Quality Summary:')
print(f'Grade: {xrp["quality_grade"]}')
print(f'Total Records: {xrp["total_records"]}')
if 'overall_score' in xrp:
    print(f'Overall Score: {xrp["overall_score"]:.2f}%')
if 'timeliness_score' in xrp:
    print(f'Timeliness Score: {xrp["timeliness_score"]}%')
if 'consistency_score' in xrp:
    print(f'Consistency Score: {xrp["consistency_score"]}%')
if 'accuracy_score' in xrp:
    print(f'Accuracy Score: {xrp["accuracy_score"]}%')
print(f'\nIssue Breakdown:')
print(f'Critical Issues: {xrp["critical_issues"]}')
print(f'High Issues: {xrp["high_issues"]}')
print(f'Medium Issues: {xrp["medium_issues"]}')
print(f'Low Issues: {xrp["low_issues"]}')
print(f'Total Issues: {xrp["total_issues"]}')
print(f'\nTime Gaps: {len(xrp["time_gaps"])} gaps found')

# Show the first few time gaps
if xrp["time_gaps"]:
    print("\nFirst 5 time gaps:")
    for i, gap in enumerate(xrp["time_gaps"][:5]):
        print(f"{i+1}. {gap['gap_size_minutes']} min gap at {gap['start_time']} - {gap['end_time']} ({gap['severity']})")

# Count spread issues
spread_issues = len(xrp["spread_issues"])
print(f'\nSpread Issues: {spread_issues}')
if spread_issues > 0:
    print(f"Sample spread issue: {xrp['spread_issues'][0]['description']} at {xrp['spread_issues'][0]['location']}")