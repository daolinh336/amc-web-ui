""" Wrapper functions that interact with the `auto-multiple-choice` CLI """

from functools import partial
import subprocess
import tempfile
import os
import sqlite3
from os import path
import shlex
from shutil import make_archive, rmtree
from typing import List


def run(args: List[str], shell=False):
    ''' Runs the provided command in the system.  The command should be split at spaces and
    provided as a list of individual words.

    If `shell` is set to `True`, the command will be executed using `sh -c {command}` and
    escaped for the shell. '''

    print('Running: {}'.format(' '.join(args)))
    if shell:
        # Shell-escape the string to avoid shell injection vulnerabilities
        args = '/bin/sh -c {}'.format(shlex.quote(' '.join(args)))
    result = subprocess.run(args, shell=shell, capture_output=True, text=True)
    if result.returncode != 0:
        cmd_str = ' '.join(args) if isinstance(args, list) else args
        print('ERROR: Command failed with exit code {}'.format(result.returncode))
        print('STDERR:\n{}'.format(result.stderr))
        raise RuntimeError('Command failed: {}\nSTDERR: {}'.format(cmd_str, result.stderr))


def make_project_dir(temp_dir: str, paths: List[str]):
    os.mkdir(path.join(temp_dir, *paths))

def create_dummy_student_list(project_dir: str):
    students_list_path = path.join(project_dir, 'cr', 'student_names.csv')
    os.makedirs(path.join(project_dir, 'cr'), exist_ok=True)
    
    students = [
        ('23021610', 'ko phai linh'),
        ('23021611', 'ko ko'),
        ('23021612', 'kimi'),
        ('23021613', 'linh'),
        ('34132724', 'linhlinh'),
        ('23021614', 'nham'),
        ('23021615', 'cua chong'),
        ('00000000', '?????????'),
    ]
    
    with open(students_list_path, mode='w', encoding='utf-8') as f:
        f.write('mssv,name\n')
        for mssv, name in students:
            f.write('{},{}\n'.format(mssv, name))
    
    return students_list_path

def create_project(project_name: str):
    """ Creates a new project in a temporary directory and returns the path to the
    created directory. """

    project_name = project_name.replace(" ", "_")

    temp_dir = tempfile.mkdtemp()

    # Set up the directory with the AMC project structure
    create_dir = partial(make_project_dir, temp_dir)
    create_dir([project_name])

    def create_inner_dir(dirs):
        merged = [project_name] + dirs
        return make_project_dir(temp_dir, merged)

    create_inner_dir(['cr'])
    create_inner_dir(['cr', 'corrections'])
    create_inner_dir(['cr', 'corrections', 'jpg'])
    create_inner_dir(['cr', 'corrections', 'pdf'])
    create_inner_dir(['cr', 'diagnostic'])
    create_inner_dir(['cr', 'zooms'])
    create_inner_dir(['data'])
    create_inner_dir(['exports'])
    create_inner_dir(['scans'])
    create_inner_dir(['copies'])

    return path.join(temp_dir, project_name)


import os
import shutil

from subprocess import run, PIPE, CalledProcessError
import os, glob, shutil


def prepare_question(project_dir, tex_file_path, mode='s,b'):
    data_dir = os.path.join(project_dir, 'data')
    output_sujet = os.path.join(project_dir, 'final_quiz.pdf')
    
    os.makedirs(data_dir, exist_ok=True)
    tex_filename = os.path.basename(tex_file_path)

    # Bước 1: Tạo PDF đề thi + file calage.xy
    result = run(
        ['auto-multiple-choice', 'prepare',
         '--mode', mode,
         '--with', 'pdflatex',
         '--filter', 'latex',
         '--data', data_dir,
         '--out-sujet', output_sujet,
         '--out-calage', 'DOC-calage.xy',
         tex_filename],
        stdout=PIPE, stderr=PIPE, text=True, cwd=project_dir
    )
    if result.returncode != 0:
        raise RuntimeError(f"AMC prepare mode={mode} thất bại:\n{result.stderr}")

    result = run(
        ['auto-multiple-choice', 'meptex',
         '--src', os.path.join(project_dir, 'DOC-calage.xy'),
         '--data', data_dir],
        stdout=PIPE, stderr=PIPE, text=True, cwd=project_dir
    )
    if result.returncode != 0:
        raise RuntimeError(f"AMC meptex thất bại:\n{result.stderr}")

    return output_sujet


def delete_project_directory(project_dir: str):
    ''' Deletes the temporary directory for the project '''

    rmtree(project_dir)

def grade_uploaded_tests(project_dir: str) -> str:
    ''' Given a project directory containing a test that has already been prepared, grades all
    tests in the `scans` subdirectory.  The resulting zooms + crops are zipped up, and the path to
    the created zipfile is returned. '''

    # Lấy danh sách file cụ thể
    scans_dir = os.path.join(project_dir, 'scans')
    scan_files = glob.glob(os.path.join(scans_dir, '*'))
    
    print(f"DEBUG: Tìm thấy {len(scan_files)} file trong thư mục scans")
    
    if not scan_files:
        print("LỖI: Không tìm thấy file nào trong thư mục scans để chấm!")
        return ""
    

    scan_pdf = os.path.join(scans_dir, "to_grade.pdf")
    output_prefix = os.path.join(scans_dir, "page")

    # Lệnh này sẽ tạo ra page-1.png, page-2.png...
    subprocess.run(['pdftocairo', '-png', '-r', '300', scan_pdf, output_prefix], check=True)

    # 2. Lấy danh sách các file PNG vừa tạo
    
    scan_files = [os.path.join(scans_dir, f) 
              for f in os.listdir(scans_dir) 
              if f.endswith('.png')]
    
    print(f"DEBUG: Tìm thấy {len(scan_files)} trang ảnh chuẩn bị chấm.")

    print(project_dir)
    print(project_dir)
    print(project_dir)
    print(project_dir)
    print(project_dir)
    analyze_cmd = [
        'auto-multiple-choice', 'analyse',
        '--projet', project_dir,
        '--prop', '0.15',
        '--bw-threshold', '0.6',
        '--ignore-redone',   
        '--force-update',    
        '--debug', '255',    # Giữ lại để mình còn soi được 83 cái ảnh kia
    ] + scan_files
    

    print(analyze_cmd)

    print("--- ĐANG QUÉT ẢNH (ANALYSE) ---")
    result_analyse = subprocess.run(analyze_cmd, capture_output=True, text=True)
    print("STDERR:", result_analyse.stderr)
    print("STDOUT:", result_analyse.stdout)



    # Compute grades
    result = subprocess.run(
        ['auto-multiple-choice', 'note', '--data', os.path.join(project_dir, 'data'), '--seuil', '0.15'],
        check=True
    )
    
    print("--- NOTE STDOUT ---")
    print(result.stdout)
    print("--- NOTE STDERR ---")
    print(result.stderr)


    students_list_path = create_dummy_student_list(project_dir)
    
    assoc_cmd = [
        'auto-multiple-choice', 'association-auto',
        '--data', os.path.join(project_dir, 'data'),
        '--liste', students_list_path,
        '--liste-key', 'mssv',
        '--notes-id', 'mssv',
        '--debug'
    ]

    result_assoc = subprocess.run(assoc_cmd, capture_output=True, text=True)

    print("=== [ASSOC STDOUT] ===")
    print(result_assoc.stdout)
    
    print("=== [ASSOC STDERR] ===")
    print(result_assoc.stderr)
        
    print(f"Assoc Return code: {result_assoc.returncode}")


    print("--- NỘI DUNG CSV ---")
    with open(students_list_path, 'r', encoding='utf-8') as f:
        print(repr(f.read()))

    assoc_db = path.join(project_dir, 'data', 'association.sqlite')
    if os.path.exists(assoc_db):
        conn = sqlite3.connect(assoc_db)
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM association_variables")
            print("VARIABLES:", cur.fetchall())
            cur.execute("SELECT * FROM association_association")
            print("ASSOCIATION:", cur.fetchall())
        except Exception as e:
            print("DB ERROR:", e)
        conn.close()
    else:
        print("association.sqlite KHÔNG TỒN TẠI!")



    annotate_cmd = [
    'auto-multiple-choice', 'annotate',
    '--project', project_dir,
    '--data', os.path.join(project_dir, 'data'),
    '--subject', os.path.join(project_dir, 'DOC-sujet.pdf'),
    '--names-file', students_list_path,
    '--association-key', 'mssv',
    '--verdict', 'Mark: %S/%M',
    ]
    subprocess.run(annotate_cmd)

    # Export grades to CSV 
    export_cmd = [
        'auto-multiple-choice', 'export',
        '--data', path.join(project_dir, 'data'),
        '--module', 'CSV',
        '--fich-noms', students_list_path,
        '--option-out', 'sep=,',
        '-o', path.join(project_dir, 'cr', 'GRADES.csv')
    ]

    print("--- ĐANG CHẠY EXPORT ---")
    result = subprocess.run(
        export_cmd, 
        capture_output=True, 
        text=True
    )
    print("STDOUT:", result.stdout if result.stdout else "(None)")
    print("STDERR:", result.stderr if result.stderr else "(None)")
    print("Return code:", result.returncode)

    # TODO: Look into automatic association

    # Zip up the directory containing crops and zooms and return it to the user.
    zip_path = path.join(project_dir, 'images')
    make_archive(zip_path, 'zip', path.join(project_dir, 'cr'))

    return path.join(project_dir, 'images.zip')