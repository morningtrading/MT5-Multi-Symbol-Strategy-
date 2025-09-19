#!/usr/bin/env python3
"""
Data Quality Controller
======================
Comprehensive quality control analysis for downloaded MT5 CSV data.
Detects gaps, anomalies, missing data, and integrity issues.

Author: Multi-Symbol Strategy Framework
Date: 2025-09-19
"""

import pandas as pd
import numpy as np
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')

@dataclass
class QualityIssue:
    """Represents a data quality issue"""
    issue_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    location: str  # row number, date range, etc.
    impact: str    # potential impact on trading
    recommendation: str

@dataclass
class SymbolQualityReport:
    """Quality report for a single symbol"""
    symbol: str
    file_path: str
    file_size_mb: float
    total_records: int
    date_range: tuple
    
    # Quality metrics
    completeness_score: float    # % of expected data present
    consistency_score: float     # consistency of OHLC data
    timeliness_score: float     # proper time sequencing
    accuracy_score: float       # data value reasonableness
    overall_quality_score: float
    
    # Detailed findings
    time_gaps: List[dict]
    data_anomalies: List[dict]
    ohlc_violations: List[dict]
    volume_issues: List[dict]
    spread_issues: List[dict]
    
    # Issues summary
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    total_issues: int
    
    quality_grade: str  # A, B, C, D, F

class DataQualityController:
    """Comprehensive data quality analysis system"""
    
    def __init__(self, data_dir: str = "CSVdata"):
        self.data_dir = data_dir
        self.raw_data_dir = os.path.join(data_dir, "raw")
        self.quality_reports = {}
        self.summary_stats = {
            "files_analyzed": 0,
            "total_records": 0,
            "total_issues": 0,
            "avg_quality_score": 0.0,
            "analysis_duration": 0.0
        }
        
        # Quality thresholds
        self.thresholds = {
            "max_gap_minutes": 5,      # Max acceptable gap between bars
            "max_spread_ratio": 0.1,   # Max spread as % of price
            "min_volume": 1,           # Minimum tick volume
            "max_price_change": 0.2,   # Max % price change between bars
            "ohlc_tolerance": 0.0001   # OHLC relationship tolerance
        }
    
    def analyze_all_files(self) -> Dict[str, SymbolQualityReport]:
        """Analyze all CSV files in the raw data directory"""
        print("🔍 DATA QUALITY CONTROLLER")
        print("=" * 60)
        
        if not os.path.exists(self.raw_data_dir):
            print(f"❌ Raw data directory not found: {self.raw_data_dir}")
            return {}
        
        csv_files = [f for f in os.listdir(self.raw_data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            print(f"❌ No CSV files found in {self.raw_data_dir}")
            return {}
        
        print(f"📊 Analyzing {len(csv_files)} CSV files")
        print("-" * 60)
        
        start_time = time.time()
        reports = {}
        
        for i, filename in enumerate(csv_files, 1):
            symbol = self.extract_symbol_from_filename(filename)
            print(f"Analyzing {symbol:<10} ({i:2}/{len(csv_files)})...", end=" ", flush=True)
            
            file_path = os.path.join(self.raw_data_dir, filename)
            report = self.analyze_single_file(file_path, symbol)
            
            if report:
                reports[symbol] = report
                grade_color = self.get_grade_color(report.quality_grade)
                print(f"{grade_color} Grade: {report.quality_grade} | Issues: {report.total_issues} | Score: {report.overall_quality_score:.1f}%")
            else:
                print("❌ Analysis failed")
        
        self.quality_reports = reports
        
        # Update summary stats
        analysis_time = time.time() - start_time
        self.summary_stats.update({
            "files_analyzed": len(reports),
            "total_records": sum(r.total_records for r in reports.values()),
            "total_issues": sum(r.total_issues for r in reports.values()),
            "avg_quality_score": sum(r.overall_quality_score for r in reports.values()) / len(reports) if reports else 0,
            "analysis_duration": analysis_time
        })
        
        print("-" * 60)
        print(f"📊 ANALYSIS COMPLETE ({analysis_time:.1f}s)")
        print(f"📈 Files: {len(reports)} | Records: {self.summary_stats['total_records']:,}")
        print(f"⚠️  Total Issues: {self.summary_stats['total_issues']} | Avg Score: {self.summary_stats['avg_quality_score']:.1f}%")
        print("=" * 60)
        
        return reports
    
    def analyze_single_file(self, file_path: str, symbol: str) -> Optional[SymbolQualityReport]:
        """Analyze a single CSV file for quality issues"""
        try:
            # Load data
            df = pd.read_csv(file_path)
            
            # Basic file info
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            total_records = len(df)
            
            # Convert datetime
            df['datetime'] = pd.to_datetime(df['datetime'])
            date_range = (df['datetime'].min(), df['datetime'].max())
            
            # Initialize quality checks
            time_gaps = self.check_time_gaps(df)
            data_anomalies = self.check_data_anomalies(df)
            ohlc_violations = self.check_ohlc_integrity(df)
            volume_issues = self.check_volume_data(df)
            spread_issues = self.check_spread_data(df)
            
            # Calculate quality scores
            completeness_score = self.calculate_completeness_score(df, time_gaps)
            consistency_score = self.calculate_consistency_score(ohlc_violations, data_anomalies)
            timeliness_score = self.calculate_timeliness_score(time_gaps)
            accuracy_score = self.calculate_accuracy_score(data_anomalies, volume_issues, spread_issues)
            
            # Overall quality score (weighted average)
            overall_quality_score = (
                completeness_score * 0.3 +
                consistency_score * 0.25 +
                timeliness_score * 0.25 +
                accuracy_score * 0.2
            )
            
            # Count issues by severity
            all_issues = time_gaps + data_anomalies + ohlc_violations + volume_issues + spread_issues
            critical_issues = len([i for i in all_issues if i.get('severity') == 'critical'])
            high_issues = len([i for i in all_issues if i.get('severity') == 'high'])
            medium_issues = len([i for i in all_issues if i.get('severity') == 'medium'])
            low_issues = len([i for i in all_issues if i.get('severity') == 'low'])
            total_issues = len(all_issues)
            
            # Assign quality grade
            quality_grade = self.assign_quality_grade(overall_quality_score, critical_issues, high_issues)
            
            return SymbolQualityReport(
                symbol=symbol,
                file_path=file_path,
                file_size_mb=file_size_mb,
                total_records=total_records,
                date_range=date_range,
                completeness_score=completeness_score,
                consistency_score=consistency_score,
                timeliness_score=timeliness_score,
                accuracy_score=accuracy_score,
                overall_quality_score=overall_quality_score,
                time_gaps=time_gaps,
                data_anomalies=data_anomalies,
                ohlc_violations=ohlc_violations,
                volume_issues=volume_issues,
                spread_issues=spread_issues,
                critical_issues=critical_issues,
                high_issues=high_issues,
                medium_issues=medium_issues,
                low_issues=low_issues,
                total_issues=total_issues,
                quality_grade=quality_grade
            )
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def check_time_gaps(self, df: pd.DataFrame) -> List[dict]:
        """Check for time gaps in the data"""
        gaps = []
        df_sorted = df.sort_values('datetime')
        
        # Calculate time differences
        time_diffs = df_sorted['datetime'].diff()
        
        # Expected 1-minute intervals
        expected_interval = timedelta(minutes=1)
        tolerance = timedelta(seconds=30)
        
        for i, diff in enumerate(time_diffs[1:], 1):
            if diff > expected_interval + tolerance:
                gap_minutes = diff.total_seconds() / 60
                severity = 'critical' if gap_minutes > 60 else 'high' if gap_minutes > 15 else 'medium'
                
                gaps.append({
                    'issue_type': 'time_gap',
                    'severity': severity,
                    'description': f'{gap_minutes:.1f} minute gap in data',
                    'location': f'Row {i}, after {df_sorted.iloc[i-1]["datetime"]}',
                    'gap_size_minutes': gap_minutes,
                    'start_time': df_sorted.iloc[i-1]['datetime'],
                    'end_time': df_sorted.iloc[i]['datetime']
                })
        
        return gaps
    
    def check_ohlc_integrity(self, df: pd.DataFrame) -> List[dict]:
        """Check OHLC data integrity"""
        violations = []
        
        for i, row in df.iterrows():
            open_price, high, low, close = row['open'], row['high'], row['low'], row['close']
            
            # Check if high is actually the highest
            if high < max(open_price, close) - self.thresholds['ohlc_tolerance']:
                violations.append({
                    'issue_type': 'ohlc_violation',
                    'severity': 'high',
                    'description': 'High price lower than open/close',
                    'location': f'Row {i}, {row["datetime"]}',
                    'values': f'O:{open_price:.2f} H:{high:.2f} L:{low:.2f} C:{close:.2f}'
                })
            
            # Check if low is actually the lowest
            if low > min(open_price, close) + self.thresholds['ohlc_tolerance']:
                violations.append({
                    'issue_type': 'ohlc_violation',
                    'severity': 'high',
                    'description': 'Low price higher than open/close',
                    'location': f'Row {i}, {row["datetime"]}',
                    'values': f'O:{open_price:.2f} H:{high:.2f} L:{low:.2f} C:{close:.2f}'
                })
            
            # Check for zero or negative prices
            if any(price <= 0 for price in [open_price, high, low, close]):
                violations.append({
                    'issue_type': 'invalid_price',
                    'severity': 'critical',
                    'description': 'Zero or negative price detected',
                    'location': f'Row {i}, {row["datetime"]}',
                    'values': f'O:{open_price:.2f} H:{high:.2f} L:{low:.2f} C:{close:.2f}'
                })
        
        return violations
    
    def check_data_anomalies(self, df: pd.DataFrame) -> List[dict]:
        """Check for data anomalies and outliers"""
        anomalies = []
        
        # Sort by datetime
        df_sorted = df.sort_values('datetime').copy()
        
        # Calculate price changes
        df_sorted['price_change'] = df_sorted['close'].pct_change()
        
        # Check for extreme price movements
        for i, row in df_sorted.iterrows():
            if pd.isna(row['price_change']):
                continue
                
            if abs(row['price_change']) > self.thresholds['max_price_change']:
                severity = 'critical' if abs(row['price_change']) > 0.5 else 'high'
                anomalies.append({
                    'issue_type': 'extreme_price_change',
                    'severity': severity,
                    'description': f'Extreme price change: {row["price_change"]:.2%}',
                    'location': f'Row {i}, {row["datetime"]}',
                    'price_change_pct': row['price_change'] * 100
                })
        
        # Check for duplicate timestamps
        duplicates = df_sorted[df_sorted['datetime'].duplicated()]
        for i, row in duplicates.iterrows():
            anomalies.append({
                'issue_type': 'duplicate_timestamp',
                'severity': 'medium',
                'description': 'Duplicate timestamp found',
                'location': f'Row {i}, {row["datetime"]}',
                'timestamp': row['datetime']
            })
        
        return anomalies
    
    def check_volume_data(self, df: pd.DataFrame) -> List[dict]:
        """Check volume data quality"""
        issues = []
        
        for i, row in df.iterrows():
            # Check for zero or missing volume
            if pd.isna(row['tick_volume']) or row['tick_volume'] < self.thresholds['min_volume']:
                issues.append({
                    'issue_type': 'low_volume',
                    'severity': 'low',
                    'description': f'Low/zero tick volume: {row["tick_volume"]}',
                    'location': f'Row {i}, {row["datetime"]}',
                    'volume': row['tick_volume']
                })
        
        return issues
    
    def check_spread_data(self, df: pd.DataFrame) -> List[dict]:
        """Check spread data reasonableness"""
        issues = []
        
        for i, row in df.iterrows():
            # Calculate spread as percentage of price
            if row['close'] > 0:
                spread_pct = (row['spread'] * 0.01) / row['close']  # Assuming spread is in points
                
                if spread_pct > self.thresholds['max_spread_ratio']:
                    issues.append({
                        'issue_type': 'excessive_spread',
                        'severity': 'medium',
                        'description': f'Excessive spread: {spread_pct:.3%} of price',
                        'location': f'Row {i}, {row["datetime"]}',
                        'spread_points': row['spread'],
                        'spread_percentage': spread_pct * 100
                    })
        
        return issues
    
    def calculate_completeness_score(self, df: pd.DataFrame, time_gaps: List[dict]) -> float:
        """Calculate data completeness score"""
        if not time_gaps:
            return 100.0
        
        # Calculate total gap time
        total_gap_minutes = sum(gap['gap_size_minutes'] for gap in time_gaps)
        
        # Calculate expected total time
        time_span_minutes = (df['datetime'].max() - df['datetime'].min()).total_seconds() / 60
        
        # Completeness = (total_time - gaps) / total_time
        completeness = max(0, (time_span_minutes - total_gap_minutes) / time_span_minutes)
        return completeness * 100
    
    def calculate_consistency_score(self, ohlc_violations: List[dict], anomalies: List[dict]) -> float:
        """Calculate data consistency score"""
        total_violations = len(ohlc_violations) + len(anomalies)
        
        if total_violations == 0:
            return 100.0
        
        # Penalty based on violation count (logarithmic scale)
        penalty = min(100, total_violations * 5 + np.log(total_violations + 1) * 10)
        return max(0, 100 - penalty)
    
    def calculate_timeliness_score(self, time_gaps: List[dict]) -> float:
        """Calculate timeliness score based on gaps"""
        if not time_gaps:
            return 100.0
        
        # Weight gaps by severity
        penalty = 0
        for gap in time_gaps:
            if gap['severity'] == 'critical':
                penalty += 20
            elif gap['severity'] == 'high':
                penalty += 10
            elif gap['severity'] == 'medium':
                penalty += 5
            else:
                penalty += 2
        
        return max(0, 100 - penalty)
    
    def calculate_accuracy_score(self, anomalies: List[dict], volume_issues: List[dict], spread_issues: List[dict]) -> float:
        """Calculate accuracy score"""
        total_issues = len(anomalies) + len(volume_issues) + len(spread_issues)
        
        if total_issues == 0:
            return 100.0
        
        # Penalty based on issue count and severity
        penalty = min(100, total_issues * 3)
        return max(0, 100 - penalty)
    
    def assign_quality_grade(self, overall_score: float, critical_issues: int, high_issues: int) -> str:
        """Assign quality grade based on score and issues"""
        if critical_issues > 0:
            return 'F'
        elif high_issues > 5:
            return 'D'
        elif overall_score >= 90:
            return 'A'
        elif overall_score >= 80:
            return 'B'
        elif overall_score >= 70:
            return 'C'
        elif overall_score >= 60:
            return 'D'
        else:
            return 'F'
    
    def get_grade_color(self, grade: str) -> str:
        """Get colored output for grade"""
        colors = {
            'A': '🟢',
            'B': '🟡', 
            'C': '🟠',
            'D': '🔴',
            'F': '💀'
        }
        return colors.get(grade, '⚪')
    
    def extract_symbol_from_filename(self, filename: str) -> str:
        """Extract symbol from filename like GEN_BTCUSD_M1_1month.csv"""
        parts = filename.replace('.csv', '').split('_')
        if len(parts) >= 2 and parts[0] == 'GEN':
            return parts[1]
        return filename.replace('.csv', '')
    
    def generate_quality_report(self) -> str:
        """Generate comprehensive quality summary"""
        if not self.quality_reports:
            return "⏳ No quality analysis completed yet"
        
        # Grade distribution
        grade_counts = {}
        for report in self.quality_reports.values():
            grade = report.quality_grade
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        # Critical symbols (grade D or F)
        critical_symbols = [symbol for symbol, report in self.quality_reports.items() 
                          if report.quality_grade in ['D', 'F']]
        
        # Top quality symbols (grade A)
        excellent_symbols = [symbol for symbol, report in self.quality_reports.items() 
                           if report.quality_grade == 'A']
        
        grade_dist = ' | '.join([f"{grade}:{count}" for grade, count in sorted(grade_counts.items())])
        excellent_str = ', '.join(excellent_symbols) if excellent_symbols else "None"
        critical_str = ', '.join(critical_symbols) if critical_symbols else "None"
        
        return (f"📊 Quality Control | Files: {self.summary_stats['files_analyzed']} | "
                f"Records: {self.summary_stats['total_records']:,} | "
                f"Avg Score: {self.summary_stats['avg_quality_score']:.1f}% | "
                f"Grades: [{grade_dist}] | "
                f"🟢 Excellent: [{excellent_str}] | "
                f"🔴 Issues: [{critical_str}] | "
                f"⚡ {self.summary_stats['analysis_duration']:.1f}s")
    
    def save_quality_report(self, filename: str = "data_quality_report.json") -> bool:
        """Save detailed quality report to JSON"""
        try:
            report_data = {
                "metadata": {
                    "analysis_date": datetime.now().isoformat(),
                    "analyzer_version": "1.0",
                    "data_directory": self.data_dir
                },
                "summary_statistics": self.summary_stats,
                "quality_thresholds": self.thresholds,
                "symbol_reports": {}
            }
            
            # Convert reports to serializable format
            for symbol, report in self.quality_reports.items():
                report_dict = asdict(report)
                # Convert datetime objects to strings
                if report_dict['date_range']:
                    report_dict['date_range'] = [
                        report_dict['date_range'][0].isoformat(),
                        report_dict['date_range'][1].isoformat()
                    ]
                report_data["symbol_reports"][symbol] = report_dict
            
            # Save to file
            output_path = os.path.join(self.data_dir, filename)
            with open(output_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            print(f"💾 Quality report saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving quality report: {e}")
            return False
    
    def get_issues_by_severity(self) -> Dict[str, List[str]]:
        """Get symbols grouped by issue severity"""
        critical = []
        high = []
        medium = []
        low = []
        
        for symbol, report in self.quality_reports.items():
            if report.critical_issues > 0:
                critical.append(symbol)
            elif report.high_issues > 0:
                high.append(symbol)
            elif report.medium_issues > 0:
                medium.append(symbol)
            else:
                low.append(symbol)
        
        return {
            'critical': critical,
            'high': high,
            'medium': medium,
            'low': low
        }

def main():
    """Main execution function"""
    print("🔍 DATA QUALITY CONTROLLER")
    print("=" * 60)
    
    # Initialize controller
    controller = DataQualityController()
    
    try:
        # Analyze all files
        reports = controller.analyze_all_files()
        
        if not reports:
            print("❌ No data analyzed")
            return
        
        # Save detailed report
        controller.save_quality_report()
        
        # Generate summary
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE QUALITY SUMMARY")
        print("=" * 80)
        print(controller.generate_quality_report())
        print("=" * 80)
        
        # Show issues by severity
        issues_by_severity = controller.get_issues_by_severity()
        if issues_by_severity['critical']:
            print(f"\n🚨 CRITICAL ISSUES: {', '.join(issues_by_severity['critical'])}")
        if issues_by_severity['high']:
            print(f"⚠️  HIGH ISSUES: {', '.join(issues_by_severity['high'])}")
        
        # Show top quality symbols
        excellent_symbols = [symbol for symbol, report in reports.items() if report.quality_grade == 'A']
        if excellent_symbols:
            print(f"\n🏆 EXCELLENT QUALITY: {', '.join(excellent_symbols)}")
        
    except Exception as e:
        print(f"❌ Quality control failed: {e}")
    
    print("\n✅ Data quality analysis complete!")

if __name__ == "__main__":
    main()