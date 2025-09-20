#!/usr/bin/env python3
"""
Copy Fixed Files to Raw Folder
===============================

Copies gap-filled files from CSVdata/fixed/ to CSVdata/raw/ with original names,
while backing up the original files to CSVdata/backup/

Author: Multi-Symbol Strategy Framework
Date: 2025-09-20
"""

import os
import shutil
from datetime import datetime

def copy_fixed_to_raw():
    print('📂 COPYING FIXED FILES TO RAW FOLDER')
    print('=' * 60)
    
    # Define directories
    fixed_dir = "CSVdata/fixed"
    raw_dir = "CSVdata/raw"
    backup_dir = "CSVdata/backup"
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # Check if directories exist
    if not os.path.exists(fixed_dir):
        print("❌ Fixed directory not found!")
        return False
    
    if not os.path.exists(raw_dir):
        print("❌ Raw directory not found!")
        return False
    
    # Get list of fixed files
    fixed_files = [f for f in os.listdir(fixed_dir) if f.endswith('_fixed.csv')]
    
    if not fixed_files:
        print("❌ No fixed files found!")
        return False
    
    print(f"📁 Found {len(fixed_files)} fixed files to copy")
    
    # Create timestamp for backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    success_count = 0
    
    for fixed_filename in fixed_files:
        # Generate original filename (remove _fixed)
        original_filename = fixed_filename.replace('_fixed', '')
        
        # Define full paths
        fixed_path = os.path.join(fixed_dir, fixed_filename)
        original_path = os.path.join(raw_dir, original_filename)
        backup_path = os.path.join(backup_dir, f"{original_filename.replace('.csv', '')}_{timestamp}_original.csv")
        
        print(f"\n📊 Processing {original_filename.replace('GEN_', '').replace('_M1_1month.csv', '')}...")
        
        try:
            # Step 1: Backup original file if it exists
            if os.path.exists(original_path):
                shutil.copy2(original_path, backup_path)
                print(f"   💾 Backed up original to: {os.path.basename(backup_path)}")
            
            # Step 2: Copy fixed file to raw directory with original name
            shutil.copy2(fixed_path, original_path)
            print(f"   ✅ Copied fixed file to: {original_filename}")
            
            # Step 3: Verify file sizes
            fixed_size = os.path.getsize(fixed_path)
            new_size = os.path.getsize(original_path)
            
            if fixed_size == new_size:
                print(f"   ✅ File size verified: {new_size:,} bytes")
                success_count += 1
            else:
                print(f"   ⚠️  Size mismatch: {fixed_size} vs {new_size}")
            
        except Exception as e:
            print(f"   ❌ Error processing {original_filename}: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COPY OPERATION COMPLETE")
    print(f"✅ Successfully copied: {success_count}/{len(fixed_files)} files")
    print(f"💾 Original files backed up to: {backup_dir}")
    print(f"📂 Fixed files now active in: {raw_dir}")
    
    if success_count == len(fixed_files):
        print("\n🎯 ALL FILES SUCCESSFULLY REPLACED!")
        print("Your raw data folder now contains the gap-filled versions.")
        print("Original files are safely backed up with timestamp.")
        return True
    else:
        print(f"\n⚠️  {len(fixed_files) - success_count} files had issues.")
        return False

def verify_replacement():
    """Verify that the replacement was successful"""
    print('\n🔍 VERIFYING REPLACEMENT SUCCESS')
    print('=' * 40)
    
    raw_dir = "CSVdata/raw"
    symbols_to_check = ["USOUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCNH"]
    
    for symbol in symbols_to_check:
        filename = f"GEN_{symbol}_M1_1month.csv"
        filepath = os.path.join(raw_dir, filename)
        
        if os.path.exists(filepath):
            # Quick check: count lines (should be 43,201 including header)
            with open(filepath, 'r') as f:
                line_count = sum(1 for line in f)
            
            if line_count > 43000:  # Should be 43,201 with header
                print(f"✅ {symbol:8}: {line_count:,} lines (gap-filled)")
            else:
                print(f"⚠️  {symbol:8}: {line_count:,} lines (may not be fixed)")
        else:
            print(f"❌ {symbol:8}: File not found")

def main():
    success = copy_fixed_to_raw()
    
    if success:
        verify_replacement()
        
        print("\n🎯 NEXT STEPS:")
        print("1. ✅ Your existing scripts will now use gap-filled data")
        print("2. 🔬 Run quality analysis to confirm: python symbol_analyzer.py quality")
        print("3. 📊 Compare backtest results with your strategies")
        print("4. 💾 Original files are safely backed up in CSVdata/backup/")

if __name__ == "__main__":
    main()