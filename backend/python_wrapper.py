""" Wrapper functions that interact with the `auto-multiple-choice` CLI """

from functools import partial
import subprocess
import tempfile
import os
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
    ''' Creates a CSV file in the provided project directory containing a dummy list of student
    names.  AMC's `note` command requires a CSV file like this, so we generate this one if
    the user doesn't provide a student list of their own. '''

    students_list_path = path.join(project_dir, 'cr', 'student_names.csv')
    with open(students_list_path, mode='w') as student_list_file:
        for i in range(0, 300):
            student_list_file.write('Student {}\n'.format(i))

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
         '--mode', 's',
         '--with', 'pdflatex',
         '--filter', 'latex',
         '--data', data_dir,
         '--n-copies', '1',
         '--out-sujet', output_sujet,
         '--out-calage', 'DOC-calage.xy',
         tex_filename],
        stdout=PIPE, stderr=PIPE, text=True, cwd=project_dir
    )
    if result.returncode != 0:
        raise RuntimeError(f"AMC prepare mode=s thất bại:\n{result.stderr}")

    # Bước 2: Ghi scoring/bareme vào DB
    result = run(
        ['auto-multiple-choice', 'prepare',
         '--mode', 'b',
         '--with', 'pdflatex',
         '--filter', 'latex',
         '--data', data_dir,
         tex_filename],
        stdout=PIPE, stderr=PIPE, text=True, cwd=project_dir
    )
    if result.returncode != 0:
        raise RuntimeError(f"AMC prepare mode=b thất bại:\n{result.stderr}")

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

    # Analyze tests
    run(['auto-multiple-choice', 'analyse', '--projet', project_dir,
         path.join(project_dir, 'scans', '*')], shell=True)

    # Compute grades
    run(['auto-multiple-choice', 'note', '--data', path.join(project_dir, 'data'),
         '--seuil', '0.15'], shell=True)

    # TODO: Take this as optional input from the user
    students_list_path = create_dummy_student_list(project_dir)

    # Export grades to CSV
    run(['auto-multiple-choice', 'export', '--data', path.join(project_dir, 'data'),
         '--module', 'CSV', '--fich-noms', students_list_path, '-o',
         path.join(project_dir, 'cr', 'GRADES.csv')], shell=True)
    
    export_cmd = [
        'auto-multiple-choice', 'export', 
        '--data', path.join(project_dir, 'data'),
        '--module', 'CSV', 
        '--fich-noms', students_list_path,
        '-o', path.join(project_dir, 'cr', 'GRADES.csv')
    ]

    print("--- ĐANG CHẠY EXPORT ---")
    result = subprocess.run(
        ' '.join(export_cmd), 
        shell=True, 
        capture_output=True, 
        text=True
    )
    print("STDOUT:", result.stdout if result.stdout else "(Trống)")
    print("STDERR:", result.stderr if result.stderr else "(Trống)")
    print("Return code:", result.returncode)

    # TODO: Look into automatic association

    # Zip up the directory containing crops and zooms and return it to the user.
    zip_path = path.join(project_dir, 'images')
    make_archive(zip_path, 'zip', path.join(project_dir, 'cr'))

    return path.join(project_dir, 'images.zip')