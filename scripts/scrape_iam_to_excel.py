#!/usr/bin/env python3
"""
Scrape IAM policies from GitHub Terraform repositories and store in Excel.
This version stores raw Terraform content in an Excel file for easier review and labeling.

Usage:
    python scrape_iam_to_excel.py --output data/scraped_policies.xlsx --max-repos 50
"""

import os
import re
import sys
import json
import time
import argparse
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from github import Github, RateLimitExceededException
from datetime import datetime

# Control characters that are illegal in the XML used by .xlsx files
# (all chars below 0x20 except TAB, LF, CR, plus 0x7f). Excel refuses to open
# files containing these, reporting the workbook as corrupted.
ILLEGAL_XML_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# GitHub token (optional, but recommended for higher rate limits)
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', None)

class TerraformPolicyScraper:
    """Scrapes IAM policies from GitHub Terraform repositories."""
    
    def __init__(self, output_file: str, max_repos: int = 50):
        self.output_file = output_file
        self.max_repos = max_repos
        self.github = Github(GITHUB_TOKEN) if GITHUB_TOKEN else Github()
        self.policies = []
        self.temp_dir = tempfile.mkdtemp(prefix='tf_scrape_')
        
    def search_repositories(self) -> List:
        """Search GitHub for Terraform repositories with IAM policies."""
        print(f"🔍 Searching GitHub for Terraform repositories with IAM policies...")
        
        # Search queries for different IAM resources
        queries = [
            "aws_iam_role language:HCL",
            "aws_iam_policy language:HCL",
            "aws_iam_role_policy language:HCL",
            "aws_iam_user_policy language:HCL",
        ]
        
        repos = set()
        
        for query in queries:
            try:
                print(f"   Query: {query}")
                results = self.github.search_repositories(
                    query=query,
                    sort='stars',
                    order='desc'
                )
                
                for repo in results[:self.max_repos]:
                    if repo.full_name not in repos:
                        repos.add(repo.full_name)
                        print(f"   ✓ Found: {repo.full_name} ({repo.stargazers_count} ⭐)")
                    
                    if len(repos) >= self.max_repos:
                        break
                        
                time.sleep(2)  # Rate limit protection
                
            except RateLimitExceededException:
                print("⚠️  GitHub rate limit exceeded. Waiting...")
                time.sleep(60)
            except Exception as e:
                print(f"⚠️  Error searching: {e}")
                continue
        
        print(f"\n✓ Found {len(repos)} unique repositories")
        return list(repos)
    
    def clone_repository(self, repo_name: str) -> Optional[Path]:
        """Clone a GitHub repository to temporary directory."""
        repo_path = Path(self.temp_dir) / repo_name.replace('/', '_')
        
        if repo_path.exists():
            return repo_path
        
        try:
            clone_url = f"https://github.com/{repo_name}.git"
            print(f"📥 Cloning {repo_name}...")
            
            subprocess.run(
                ['git', 'clone', '--depth', '1', clone_url, str(repo_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60
            )
            
            return repo_path if repo_path.exists() else None
            
        except subprocess.TimeoutExpired:
            print(f"⚠️  Timeout cloning {repo_name}")
            return None
        except Exception as e:
            print(f"⚠️  Error cloning {repo_name}: {e}")
            return None
    
    def find_iam_files(self, repo_path: Path) -> List[Path]:
        """Find Terraform files containing IAM policy definitions."""
        iam_files = []
        
        # Search for .tf files
        for tf_file in repo_path.rglob('*.tf'):
            try:
                content = tf_file.read_text(encoding='utf-8', errors='ignore')
                
                # Check if file contains IAM resource definitions
                iam_keywords = [
                    'resource "aws_iam_role"',
                    'resource "aws_iam_policy"',
                    'resource "aws_iam_role_policy"',
                    'resource "aws_iam_user_policy"',
                    'aws_iam_policy_document',
                ]
                
                if any(keyword in content for keyword in iam_keywords):
                    iam_files.append(tf_file)
                    
            except Exception as e:
                continue
        
        return iam_files
    
    def run_checkov(self, file_path: Path) -> str:
        """Run Checkov security scanner on a Terraform file."""
        try:
            result = subprocess.run(
                ['checkov', '-f', str(file_path), '--quiet', '--compact'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Extract relevant findings
            output = result.stdout
            if 'Passed checks' in output or 'Failed checks' in output:
                return output
            return "No findings"
            
        except subprocess.TimeoutExpired:
            return "Timeout"
        except FileNotFoundError:
            return "Checkov not installed"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def extract_policy_content(self, file_path: Path) -> str:
        """Extract and return the full Terraform file content."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Strip control characters that are illegal in xlsx XML, and
            # normalise line endings so the content survives an Excel/CSV round
            # trip without corrupting the workbook.
            content = ILLEGAL_XML_CHARS.sub('', content)
            content = content.replace('\r\n', '\n').replace('\r', '\n')

            # Check for Excel cell size limit (32,767 characters)
            if len(content) > 32000:
                print(f"   ⚠️  File too large ({len(content)} chars), truncating: {file_path.name}")
                content = content[:32000] + "\n\n... [TRUNCATED]"
            
            return content
            
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def process_repository(self, repo_name: str):
        """Process a single repository and extract IAM policies."""
        repo_path = self.clone_repository(repo_name)
        
        if not repo_path:
            return
        
        # Find IAM-related Terraform files
        iam_files = self.find_iam_files(repo_path)
        print(f"   Found {len(iam_files)} IAM-related Terraform files")
        
        for tf_file in iam_files:
            try:
                # Extract content
                content = self.extract_policy_content(tf_file)
                
                # Run Checkov scan
                print(f"   📋 Processing: {tf_file.name}")
                checkov_result = self.run_checkov(tf_file)
                
                # Get relative path within repo
                rel_path = tf_file.relative_to(repo_path)
                
                # Add to collection
                policy_data = {
                    'filename': tf_file.name,
                    'source_repo': repo_name,
                    'source_path': str(rel_path),
                    'content': content,
                    'content_length': len(content),
                    'checkov_findings': checkov_result,
                    'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'vulnerable': None,  # To be labeled manually
                    'confidence': None,  # To be filled during labeling
                    'notes': '',         # Reviewer notes
                }
                
                self.policies.append(policy_data)
                print(f"   ✓ Added: {tf_file.name} ({len(content)} chars)")
                
            except Exception as e:
                print(f"   ⚠️  Error processing {tf_file}: {e}")
                continue
        
        # Cleanup cloned repo
        try:
            shutil.rmtree(repo_path)
        except:
            pass
    
    def save_to_excel(self):
        """Save collected policies to Excel file."""
        if not self.policies:
            print("⚠️  No policies found to save")
            return
        
        print(f"\n💾 Saving {len(self.policies)} policies to Excel...")
        
        # Create DataFrame
        df = pd.DataFrame(self.policies)
        
        # Reorder columns for better readability
        column_order = [
            'filename',
            'source_repo',
            'source_path',
            'content',
            'content_length',
            'vulnerable',
            'confidence',
            'notes',
            'checkov_findings',
            'scraped_date'
        ]
        df = df[column_order]
        
        # Save to Excel with formatting
        output_path = Path(self.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prefer xlsxwriter: it produces a standards-compliant OOXML package
        # (shared strings + explicit styles) that opens reliably in Excel mobile,
        # Excel desktop/online, Google Sheets and LibreOffice. Fall back to
        # openpyxl only if xlsxwriter is unavailable.
        try:
            import xlsxwriter  # noqa: F401
            excel_engine = 'xlsxwriter'
        except ImportError:
            excel_engine = 'openpyxl'

        with pd.ExcelWriter(output_path, engine=excel_engine) as writer:
            df.to_excel(writer, index=False, sheet_name='IAM_Policies')
            
            # Get the worksheet
            worksheet = writer.sheets['IAM_Policies']

            # Adjust column widths (engine-aware: xlsxwriter vs openpyxl differ).
            widths = [30, 35, 40, 80, 15, 12, 12, 40, 50, 20]
            if excel_engine == 'xlsxwriter':
                for idx, width in enumerate(widths):
                    worksheet.set_column(idx, idx, width)
            else:
                from openpyxl.utils import get_column_letter
                for idx, width in enumerate(widths, start=1):
                    worksheet.column_dimensions[get_column_letter(idx)].width = width
        
        # Always write a CSV backup next to the xlsx. CSV opens reliably in any
        # tool and acts as a safety net if the xlsx is ever reported corrupted.
        csv_path = output_path.with_suffix('.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"✓ Saved to: {output_path}")
        print(f"✓ CSV backup: {csv_path}")
        print(f"\n📊 Summary:")
        print(f"   Total policies: {len(df)}")
        print(f"   Unique repositories: {df['source_repo'].nunique()}")
        print(f"   Average content length: {df['content_length'].mean():.0f} chars")
        print(f"   Max content length: {df['content_length'].max()} chars")
        
        # Check for truncated files
        truncated = df[df['content'].str.contains('TRUNCATED', na=False)]
        if len(truncated) > 0:
            print(f"   ⚠️  {len(truncated)} files were truncated (>32K chars)")
    
    def cleanup(self):
        """Clean up temporary directory."""
        try:
            shutil.rmtree(self.temp_dir)
            print(f"✓ Cleaned up temporary files")
        except Exception as e:
            print(f"⚠️  Error cleaning up: {e}")
    
    def run(self):
        """Main execution flow."""
        print("=" * 70)
        print("Terraform IAM Policy Scraper → Excel")
        print("=" * 70)
        
        try:
            # Search repositories
            repos = self.search_repositories()
            
            if not repos:
                print("⚠️  No repositories found")
                return
            
            # Process each repository
            print(f"\n📦 Processing {len(repos)} repositories...\n")
            for idx, repo_name in enumerate(repos, 1):
                print(f"\n[{idx}/{len(repos)}] {repo_name}")
                print("-" * 70)
                self.process_repository(repo_name)
                time.sleep(1)  # Rate limit protection
            
            # Save results
            self.save_to_excel()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            if self.policies:
                print("Saving partial results...")
                self.save_to_excel()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()


def main():
    parser = argparse.ArgumentParser(
        description='Scrape IAM policies from GitHub Terraform repos to Excel'
    )
    parser.add_argument(
        '--output',
        default='data/scraped_policies.xlsx',
        help='Output Excel file path (default: data/scraped_policies.xlsx)'
    )
    parser.add_argument(
        '--max-repos',
        type=int,
        default=50,
        help='Maximum number of repositories to scrape (default: 50)'
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    try:
        import pandas
        import openpyxl
        from github import Github
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nInstall required packages:")
        print("  pip install pandas openpyxl PyGithub")
        sys.exit(1)
    
    # Run scraper
    scraper = TerraformPolicyScraper(
        output_file=args.output,
        max_repos=args.max_repos
    )
    scraper.run()
    
    print("\n" + "=" * 70)
    print("✓ Scraping complete!")
    print("=" * 70)
    print(f"\nNext steps:")
    print(f"1. Open: {args.output}")
    print(f"2. Review and label policies (vulnerable column: True/False)")
    print(f"3. Add confidence level (High/Medium/Low)")
    print(f"4. Add notes for interesting cases")
    print(f"5. Run: python scripts/excel_to_training_data.py")


if __name__ == '__main__':
    main()
