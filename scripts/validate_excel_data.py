#!/usr/bin/env python3
"""
Validate Excel data before conversion to training format.
Checks for common issues like missing data, invalid labels, truncated content, etc.

Usage:
    python validate_excel_data.py --input data/scraped_policies.xlsx
"""

import sys
import argparse
from pathlib import Path
import pandas as pd


class ExcelDataValidator:
    """Validates Excel policy data for quality issues."""
    
    def __init__(self, input_file: str):
        self.input_file = Path(input_file)
        self.issues = []
        self.warnings = []
        self.df = None
    
    def load_data(self) -> bool:
        """Load Excel data."""
        if not self.input_file.exists():
            print(f"❌ File not found: {self.input_file}")
            return False
        
        try:
            self.df = pd.read_excel(self.input_file, sheet_name='IAM_Policies')
            print(f"✓ Loaded {len(self.df)} rows from {self.input_file}")
            return True
        except Exception as e:
            print(f"❌ Error loading Excel: {e}")
            return False
    
    def check_required_columns(self):
        """Check for required columns."""
        print("\n📋 Checking required columns...")
        
        required = ['filename', 'content', 'vulnerable']
        recommended = ['source_repo', 'confidence', 'notes']
        
        missing_required = [col for col in required if col not in self.df.columns]
        missing_recommended = [col for col in recommended if col not in self.df.columns]
        
        if missing_required:
            self.issues.append(f"Missing required columns: {missing_required}")
            print(f"   ❌ Missing required: {missing_required}")
        else:
            print(f"   ✓ All required columns present")
        
        if missing_recommended:
            self.warnings.append(f"Missing recommended columns: {missing_recommended}")
            print(f"   ⚠️  Missing recommended: {missing_recommended}")
    
    def check_labeling_status(self):
        """Check labeling progress and distribution."""
        print("\n🏷️  Checking labeling status...")
        
        total = len(self.df)
        labeled = self.df['vulnerable'].notna().sum()
        unlabeled = total - labeled
        
        print(f"   Total policies: {total}")
        print(f"   Labeled: {labeled} ({labeled/total*100:.1f}%)")
        print(f"   Unlabeled: {unlabeled} ({unlabeled/total*100:.1f}%)")
        
        if labeled == 0:
            self.issues.append("No policies labeled yet")
            print(f"   ❌ No policies labeled!")
            return
        
        if unlabeled > labeled:
            self.warnings.append(f"More unlabeled ({unlabeled}) than labeled ({labeled})")
            print(f"   ⚠️  Most policies still unlabeled")
        
        # Check distribution
        vulnerable = self.df['vulnerable'].sum()
        safe = (self.df['vulnerable'] == False).sum()
        
        print(f"\n   Label distribution:")
        print(f"   Vulnerable: {vulnerable} ({vulnerable/labeled*100:.1f}%)")
        print(f"   Safe: {safe} ({safe/labeled*100:.1f}%)")
        
        if vulnerable == 0 or safe == 0:
            self.issues.append("Only one class labeled (need both vulnerable and safe)")
            print(f"   ❌ Only one class present!")
        else:
            ratio = vulnerable / safe if safe > 0 else float('inf')
            print(f"   Vulnerable/Safe ratio: {ratio:.2f}")
            
            if ratio < 0.3 or ratio > 3.0:
                self.warnings.append(f"Imbalanced dataset (ratio: {ratio:.2f})")
                print(f"   ⚠️  Dataset is imbalanced")
    
    def check_content_quality(self):
        """Check content field for issues."""
        print("\n📄 Checking content quality...")
        
        # Empty content
        empty = self.df['content'].isna().sum()
        if empty > 0:
            self.issues.append(f"{empty} rows with empty content")
            print(f"   ❌ {empty} rows have empty content")
        else:
            print(f"   ✓ No empty content")
        
        # Truncated content
        truncated = self.df['content'].astype(str).str.contains('TRUNCATED', na=False).sum()
        if truncated > 0:
            self.warnings.append(f"{truncated} files were truncated (>32K chars)")
            print(f"   ⚠️  {truncated} files truncated (Excel cell limit)")
        
        # Content length statistics
        lengths = self.df['content'].astype(str).str.len()
        print(f"\n   Content length statistics:")
        print(f"   Min: {lengths.min()} chars")
        print(f"   Max: {lengths.max()} chars")
        print(f"   Mean: {lengths.mean():.0f} chars")
        print(f"   Median: {lengths.median():.0f} chars")
        
        # Very short content (likely errors)
        very_short = (lengths < 100).sum()
        if very_short > 0:
            self.warnings.append(f"{very_short} files with suspiciously short content (<100 chars)")
            print(f"   ⚠️  {very_short} files are very short (<100 chars)")
    
    def check_duplicate_files(self):
        """Check for duplicate filenames."""
        print("\n🔍 Checking for duplicates...")
        
        duplicates = self.df['filename'].duplicated().sum()
        if duplicates > 0:
            self.warnings.append(f"{duplicates} duplicate filenames")
            print(f"   ⚠️  {duplicates} duplicate filenames found")
            
            # Show duplicates
            dup_files = self.df[self.df['filename'].duplicated(keep=False)]['filename'].unique()
            print(f"   Duplicates: {list(dup_files)[:5]}...")
        else:
            print(f"   ✓ No duplicate filenames")
    
    def check_confidence_notes(self):
        """Check confidence and notes fields."""
        print("\n📝 Checking confidence and notes...")
        
        if 'confidence' in self.df.columns:
            labeled_df = self.df[self.df['vulnerable'].notna()]
            with_confidence = labeled_df['confidence'].notna().sum()
            print(f"   Labeled policies with confidence: {with_confidence}/{len(labeled_df)}")
            
            if with_confidence < len(labeled_df) * 0.5:
                self.warnings.append("Less than 50% of labeled policies have confidence ratings")
        
        if 'notes' in self.df.columns:
            labeled_df = self.df[self.df['vulnerable'].notna()]
            with_notes = labeled_df['notes'].notna().sum()
            print(f"   Labeled policies with notes: {with_notes}/{len(labeled_df)}")
    
    def check_checkov_results(self):
        """Check Checkov findings."""
        print("\n🔒 Checking Checkov results...")
        
        if 'checkov_findings' not in self.df.columns:
            self.warnings.append("No Checkov findings column")
            return
        
        no_findings = self.df['checkov_findings'].astype(str).str.contains('No findings', na=False).sum()
        errors = self.df['checkov_findings'].astype(str).str.contains('Error|Timeout', na=False).sum()
        
        print(f"   Clean (no findings): {no_findings}")
        print(f"   Errors/Timeouts: {errors}")
        
        if errors > len(self.df) * 0.5:
            self.warnings.append("More than 50% Checkov scans failed")
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        
        if not self.issues and not self.warnings:
            print("✅ All checks passed! Data looks good.")
        else:
            if self.issues:
                print(f"\n❌ CRITICAL ISSUES ({len(self.issues)}):")
                for issue in self.issues:
                    print(f"   • {issue}")
            
            if self.warnings:
                print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
                for warning in self.warnings:
                    print(f"   • {warning}")
        
        print("\n" + "=" * 70)
        
        if self.issues:
            print("\n❌ Fix critical issues before converting to training data")
            return False
        elif self.warnings:
            print("\n⚠️  Review warnings, but data can be converted")
            return True
        else:
            print("\n✅ Ready for conversion!")
            return True
    
    def run(self) -> bool:
        """Run all validation checks."""
        print("=" * 70)
        print("Excel Data Validation")
        print("=" * 70)
        
        if not self.load_data():
            return False
        
        self.check_required_columns()
        self.check_labeling_status()
        self.check_content_quality()
        self.check_duplicate_files()
        self.check_confidence_notes()
        self.check_checkov_results()
        
        return self.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description='Validate Excel policy data before conversion'
    )
    parser.add_argument(
        '--input',
        default='data/scraped_policies.xlsx',
        help='Excel file to validate'
    )
    
    args = parser.parse_args()
    
    validator = ExcelDataValidator(args.input)
    success = validator.run()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
