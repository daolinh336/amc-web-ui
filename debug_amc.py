#!/usr/bin/env python3
"""
Script để debug AMC analyse và association
"""
import subprocess
import os
import glob
import tempfile
import shutil

def debug_amc_scan(pdf_path, project_dir=None):
    """Debug AMC analyse trên 1 file PDF"""

    if not project_dir:
        project_dir = tempfile.mkdtemp(prefix='amc_debug_')

    print(f"Project dir: {project_dir}")
    print(f"PDF file: {pdf_path}")

    # Check AMC version
    version_cmd = ['auto-multiple-choice', '--version']
    try:
        version_result = subprocess.run(version_cmd, capture_output=True, text=True)
        print(f"AMC version: {version_result.stdout.strip()}")
    except Exception as e:
        print(f"Cannot get AMC version: {e}")

    # Tạo thư mục scans
    scans_dir = os.path.join(project_dir, 'scans')
    os.makedirs(scans_dir, exist_ok=True)

    # Copy PDF vào scans
    shutil.copy(pdf_path, os.path.join(scans_dir, 'to_grade.pdf'))

    # Chạy analyse với params giống hệ thống
    analyze_cmd = [
        'auto-multiple-choice', 'analyse',
        '--projet', project_dir,
        '--prop', '0.9',
        '--bw-threshold', '0.6',
        os.path.join(scans_dir, 'to_grade.pdf')
    ]

    print("Running analyse...")
    print(f"Command: {' '.join(analyze_cmd)}")
    result = subprocess.run(analyze_cmd, capture_output=True, text=True)
    print("Return code:", result.returncode)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # Check files created
    data_dir = os.path.join(project_dir, 'data')
    if os.path.exists(data_dir):
        files = os.listdir(data_dir)
        print(f"Files in data/: {files}")

        # Check layout files
        layout_files = [f for f in files if 'layout' in f.lower()]
        print(f"Layout files: {layout_files}")

        # Check capture.sqlite
        capture_db = os.path.join(data_dir, 'capture.sqlite')
        if os.path.exists(capture_db):
            print("capture.sqlite exists")
            import sqlite3
            try:
                conn = sqlite3.connect(capture_db)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cur.fetchall()
                print(f"Tables: {tables}")
                conn.close()
            except Exception as e:
                print(f"Error reading capture.db: {e}")
        else:
            print("capture.sqlite does NOT exist")

    return project_dir

if __name__ == "__main__":
    # Thay đường dẫn PDF của bạn
    pdf_file = r"d:\UET\why\amc-web-ui\test_questions.pdf"  # Thay bằng file PDF thật
    if os.path.exists(pdf_file):
        debug_amc_scan(pdf_file)
    else:
        print(f"PDF file not found: {pdf_file}")
        print("Please update the pdf_file path in the script")