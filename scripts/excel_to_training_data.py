#!/usr/bin/env python3
"""
Convert labeled Excel policies to JSON training data format.
Reads the labeled Excel file and generates individual JSON policy files
plus a LABELS.json file for training.

Usage:
    python excel_to_training_data.py --input data/scraped_policies.xlsx --output data/train_policies
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List
import pandas as pd
from datetime import datetime


class ExcelToTrainingConverter:
    """Converts labeled Excel data to PolicyGraph training format."""
    
    def __init__(self, input_file: str, output_dir: str, prefix: str = 'scraped'):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.prefix = prefix
        self.stats = {
            'total_rows': 0,
            'labeled_rows': 0,
            'vulnerable_count': 0,
            'safe_count': 0,
            'skipped_unlabeled': 0,
            'skipped_invalid': 0,
            'files_created': 0,
        }
    
    def validate_excel_file(self) -> bool:
        """Validate that the Excel file exists and has required columns."""
        if not self.input_file.exists():
            print(f"❌ Input file not found: {self.input_file}")
            return False
        
        print(f"✓ Found input file: {self.input_file}")
        return True
    
    def load_excel_data(self) -> pd.DataFrame:
        """Load and validate Excel data."""
        print(f"\n📂 Loading Excel data...")
        
        try:
            df = pd.read_excel(self.input_file, sheet_name='IAM_Policies')
            self.stats['total_rows'] = len(df)
            
            print(f"✓ Loaded {len(df)} rows")
            
            # Check required columns
            required_columns = ['filename', 'content', 'vulnerable']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"❌ Missing required columns: {missing_columns}")
                print(f"   Available columns: {list(df.columns)}")
                return None
            
            print(f"✓ Required columns present")
            
            return df
            
        except Exception as e:
            print(f"❌ Error loading Excel: {e}")
            return None
    
    def filter_labeled_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter to only labeled rows with valid data."""
        print(f"\n🔍 Filtering labeled data...")
        
        # Show initial distribution
        print(f"\nInitial data distribution:")
        print(f"   Total rows: {len(df)}")
        print(f"   Labeled (vulnerable=True): {df['vulnerable'].sum() if 'vulnerable' in df else 0}")
        print(f"   Labeled (vulnerable=False): {(df['vulnerable'] == False).sum() if 'vulnerable' in df else 0}")
        print(f"   Unlabeled (null): {df['vulnerable'].isna().sum() if 'vulnerable' in df else len(df)}")
        
        # Filter to labeled rows only
        labeled_df = df[df['vulnerable'].notna()].copy()
        self.stats['skipped_unlabeled'] = len(df) - len(labeled_df)
        
        print(f"\n✓ Found {len(labeled_df)} labeled policies")
        print(f"   Skipped {self.stats['skipped_unlabeled']} unlabeled rows")
        
        # Validate boolean values
        invalid_labels = labeled_df[~labeled_df['vulnerable'].isin([True, False, 'True', 'False', 1, 0])]
        if len(invalid_labels) > 0:
            print(f"⚠️  Found {len(invalid_labels)} rows with invalid labels:")
            print(invalid_labels[['filename', 'vulnerable']])
            labeled_df = labeled_df[labeled_df['vulnerable'].isin([True, False, 'True', 'False', 1, 0])]
            self.stats['skipped_invalid'] = len(invalid_labels)
        
        # Normalize to boolean
        labeled_df['vulnerable'] = labeled_df['vulnerable'].astype(bool)
        
        # Count final distribution
        self.stats['vulnerable_count'] = labeled_df['vulnerable'].sum()
        self.stats['safe_count'] = (~labeled_df['vulnerable']).sum()
        
        print(f"\nFinal labeled distribution:")
        print(f"   Vulnerable: {self.stats['vulnerable_count']}")
        print(f"   Safe: {self.stats['safe_count']}")
        print(f"   Balance ratio: {self.stats['vulnerable_count']/(self.stats['safe_count']+0.001):.2f}")
        
        return labeled_df
    
    def create_policy_files(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Create individual policy JSON files and collect metadata."""
        print(f"\n📝 Creating policy files...")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        labels = {}
        
        for idx, row in df.iterrows():
            # Generate filename
            policy_filename = f"{self.prefix}_policy_{idx:04d}.json"
            policy_path = self.output_dir / policy_filename
            
            # Create policy JSON structure
            policy_data = {
                'type': 'terraform',
                'content': row['content'],
                'metadata': {
                    'original_filename': row['filename'],
                    'source_repo': row.get('source_repo', 'unknown'),
                    'source_path': row.get('source_path', 'unknown'),
                    'scraped_date': str(row.get('scraped_date', 'unknown')),
                    'conversion_date': datetime.now().isoformat(),
                }
            }
            
            # Save policy file
            try:
                with open(policy_path, 'w', encoding='utf-8') as f:
                    json.dump(policy_data, f, indent=2, ensure_ascii=False)
                
                self.stats['files_created'] += 1
                
                if self.stats['files_created'] % 10 == 0:
                    print(f"   Created {self.stats['files_created']} files...")
                
            except Exception as e:
                print(f"⚠️  Error creating {policy_filename}: {e}")
                continue
            
            # Add to labels dictionary
            labels[policy_filename] = {
                'label': 'vulnerable' if row['vulnerable'] else 'safe',
                'source': row.get('source_repo', 'unknown'),
                'source_path': row.get('source_path', 'unknown'),
                'confidence': str(row.get('confidence', 'unknown')),
                'notes': str(row.get('notes', '')),
                'checkov_findings': str(row.get('checkov_findings', 'none'))[:200],  # Truncate for readability
            }
        
        print(f"✓ Created {self.stats['files_created']} policy files")
        
        return labels
    
    def create_labels_file(self, labels: Dict[str, Dict]):
        """Create LABELS.json file."""
        print(f"\n📋 Creating LABELS.json...")
        
        labels_path = self.output_dir / 'LABELS.json'
        
        try:
            with open(labels_path, 'w', encoding='utf-8') as f:
                json.dump(labels, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Created: {labels_path}")
            print(f"   Total labels: {len(labels)}")
            
        except Exception as e:
            print(f"❌ Error creating LABELS.json: {e}")
    
    def create_metadata_file(self):
        """Create conversion metadata file."""
        metadata = {
            'conversion_date': datetime.now().isoformat(),
            'input_file': str(self.input_file),
            'output_directory': str(self.output_dir),
            'statistics': self.stats,
            'schema_version': '1.0',
            'notes': 'Converted from Excel using excel_to_training_data.py'
        }
        
        metadata_path = self.output_dir / 'CONVERSION_METADATA.json'
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✓ Created metadata: {metadata_path}")
    
    def print_summary(self):
        """Print conversion summary."""
        print("\n" + "=" * 70)
        print("CONVERSION SUMMARY")
        print("=" * 70)
        print(f"Input file:        {self.input_file}")
        print(f"Output directory:  {self.output_dir}")
        print(f"\nStatistics:")
        print(f"   Total rows in Excel:     {self.stats['total_rows']}")
        print(f"   Labeled rows:            {self.stats['labeled_rows']}")
        print(f"   Files created:           {self.stats['files_created']}")
        print(f"\nLabel distribution:")
        print(f"   Vulnerable policies:     {self.stats['vulnerable_count']}")
        print(f"   Safe policies:           {self.stats['safe_count']}")
        print(f"\nSkipped:")
        print(f"   Unlabeled rows:          {self.stats['skipped_unlabeled']}")
        print(f"   Invalid labels:          {self.stats['skipped_invalid']}")
        
        # Calculate balance
        if self.stats['safe_count'] > 0:
            balance_ratio = self.stats['vulnerable_count'] / self.stats['safe_count']
            print(f"\nDataset balance:")
            print(f"   Vulnerable/Safe ratio:   {balance_ratio:.2f}")
            if balance_ratio < 0.5 or balance_ratio > 2.0:
                print(f"   ⚠️  Dataset is imbalanced! Consider balancing before training.")
            else:
                print(f"   ✓ Dataset is reasonably balanced")
        
        print("=" * 70)
    
    def run(self) -> bool:
        """Main execution flow."""
        print("=" * 70)
        print("Excel to Training Data Converter")
        print("=" * 70)
        
        # Validate input
        if not self.validate_excel_file():
            return False
        
        # Load data
        df = self.load_excel_data()
        if df is None:
            return False
        
        # Filter labeled data
        labeled_df = self.filter_labeled_data(df)
        if len(labeled_df) == 0:
            print("❌ No labeled data found. Please label policies in Excel first.")
            return False
        
        self.stats['labeled_rows'] = len(labeled_df)
        
        # Create policy files
        labels = self.create_policy_files(labeled_df)
        
        # Create LABELS.json
        self.create_labels_file(labels)
        
        # Create metadata
        self.create_metadata_file()
        
        # Print summary
        self.print_summary()
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Convert labeled Excel policies to training data format'
    )
    parser.add_argument(
        '--input',
        default='data/scraped_policies.xlsx',
        help='Input Excel file with labeled policies'
    )
    parser.add_argument(
        '--output',
        default='data/train_policies',
        help='Output directory for JSON files and LABELS.json'
    )
    parser.add_argument(
        '--prefix',
        default='scraped',
        help='Prefix for generated policy filenames (default: scraped)'
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    try:
        import pandas
        import openpyxl
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nInstall required packages:")
        print("  pip install pandas openpyxl")
        sys.exit(1)
    
    # Run converter
    converter = ExcelToTrainingConverter(
        input_file=args.input,
        output_dir=args.output,
        prefix=args.prefix
    )
    
    success = converter.run()
    
    if success:
        print("\n✓ Conversion complete!")
        print("\nNext steps:")
        print("1. Verify the generated files in:", args.output)
        print("2. Check LABELS.json for correct format")
        print("3. Run training: python -m policygraph.train --config config.yaml")
    else:
        print("\n❌ Conversion failed")
        sys.exit(1)


if __name__ == '__main__':
    main()