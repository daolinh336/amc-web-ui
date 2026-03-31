''' Contains utilities for converting the intermediate JSON representation into TeX content. '''

from typing import List

HEADER_1 = r'''
\RequirePackage{etex}
\documentclass[a4paper]{article}

\usepackage[utf8]{inputenc}
\usepackage[vietnamese]{babel}
\usepackage[T1]{fontenc}
\usepackage{amssymb}
\usepackage{pifont}
\usepackage{tikz}
\usepackage{xcolor}
\usepackage[box,completemulti]{automultiplechoice}

% Chỉ dùng các tham số cơ bản mà bản 1.5.0 chắc chắn hỗ trợ
\AMCboxStyle{shape=square, size=2.5ex, color=black}

\begin{document}
\AMCrandomseed{1237893}
\setdefaultgroupmode{withoutreplacement}
'''

HEADER_2 = r'''
\onecopy{COPIES}{

%%% beginning of the test sheet header:

\noindent{\bf QCM  \hfill TEST}

\vspace*{.5cm}
\begin{minipage}{.4\linewidth}
  \centering\large\bf Test\ Examination on TODAY'S DATE
\end{minipage}
\hfill
\namefield{\fbox{
     \begin{minipage}{.5\linewidth}
        Firstname and lastname:

        \vspace*{.5cm}\dotfill
        \vspace*{1mm}
    \end{minipage}
  }}

\begin{center}\em
Duration : 10 minutes.

  No notes allowed. The use of electronic calculators is forbidden.

  Questions using the sign \multiSymbole{} may have
  zero, one or several correct answers.  Other questions have a single correct answer.
\end{center}
\vspace{1ex}

%%% end of the header
'''


TRAILER = r'''
}

\end{document}
'''

def create_answer(text: str, is_correct: bool):
    # Tuyệt đối KHÔNG để khoảng trắng ở đầu chuỗi này
    cmd = 'correctchoice' if is_correct else 'wrongchoice'
    return f"\\{cmd}{{{text}}}"

def parse_question_dict(questions: dict, index: int = 1) -> str:
    # Nối các đáp án, mỗi đáp án một dòng, sát lề trái
    answers = '\n'.join([create_answer(a['answerText'], a['correct']) for a in questions['answers']])

    question_type = 'questionmult' if sum(1 for a in questions['answers'] if a['correct']) > 1 else 'question'
    clean_topic = "".join(filter(str.isalnum, questions.get('topic') or 'default'))

    # Dùng f-string và đưa tất cả các lệnh nhạy cảm sát lề trái của file .tex
    # Lưu ý: Không thụt lề bên trong các dòng có lệnh \begin, \end, \choice
    question_spec = rf'''
\element{{{clean_topic}}}{{
\begin{{{question_type}}}{{q{index}}}
{questions['questionText']}
\begin{{choices}}
{answers}
\end{{choices}}
\end{{{question_type}}}
}}
'''
    return question_spec

# def parse_question_dict_list(question_list: List[dict], copies: int = 10) -> str:
#     ''' Given a list of questions in the schema detailed in the `parse_question_dict` function,
#     parses them all into LaTeX, combines them with the header and trailer required to produce
#     a valid AMC .tex file, and returns the generated LaTeX source code as a string. '''

#     output = ''
#     for (i, question) in enumerate(question_list, start=1):
#         output += parse_question_dict(question, i)
#         output += '\n'

#     groups = ''
#     topics = sorted(list(set(map(lambda q: "".join(filter(str.isalnum, q.get('topic') or 'default')), question_list))))
#     for topic in topics:
#         groups += '\\shufflegroup{{{}}}\n'.format(topic)
#         groups += '\\insertgroup{{{}}}\n\n'.format(topic)

#     our_header2 = HEADER_2.replace('COPIES', str(copies))
#     return HEADER_1 + output + our_header2 + groups + TRAILER


def parse_question_dict_list(question_list: List[dict], copies: int = 10) -> str:
    questions_definition = ''
    for (i, question) in enumerate(question_list, start=1):
        questions_definition += parse_question_dict(question, i) + '\n'

    groups_insertion = ''
    topics = sorted(list(set(map(lambda q: "".join(filter(str.isalnum, q.get('topic') or 'default')), question_list))))
    for topic in topics:
        groups_insertion += f'\\shufflegroup{{{topic}}}\n'
        groups_insertion += f'\\insertgroup{{{topic}}}\n\n'
    
    our_header2 = HEADER_2.replace('COPIES', str(copies))
    
    return HEADER_1 + questions_definition + our_header2 + groups_insertion + TRAILER



def force_sync_amc_layout(project_dir, db_path):
    """
    Hàm này ép buộc nạp tọa độ từ file .xy vào SQLite 
    bất kể AMC có đang ở chế độ CATALOG hay không.
    """
    # 1. Tìm file tọa độ chuẩn (thường là *-calage.xy)
    calage_files = glob.glob(os.path.join(project_dir, "*-calage.xy"))
    if not calage_files:
        print("Lỗi: Không tìm thấy file tọa độ *-calage.xy")
        return False
    
    xy_file = calage_files[0]
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"Đang tự động hóa nạp dữ liệu từ {xy_file}...")

    with open(xy_file, 'r') as f:
        for line in f:
            # Bước A: Tự động đăng ký "Khung xương" câu hỏi nếu chưa có
            # Tìm pattern: :case:q(số):
            q_match = re.search(r':case:q(\d+):', line)
            if q_match:
                q_id = int(q_match.group(1))
                q_name = f"q{q_id}"
                cursor.execute("INSERT OR IGNORE INTO layout_question (question, name) VALUES (?, ?)", (q_id, q_name))

            # Bước B: Nạp "Tọa độ" vào bảng layout_box
            # Pattern tracepos chuẩn của AMC
            t_match = re.search(r'tracepos\{(\d+)/(\d+):case:q(\d+):(\d+),(\d+)\}\{(\d+)sp\}\{(\d+)sp\}', line)
            if t_match:
                std, pg, q_idx, rank, ans, x_sp, y_sp = t_match.groups()
                
                # Chuyển đổi đơn vị sp sang point (chuẩn của AMC layout)
                x_val = float(x_sp) / 65536
                y_val = float(y_sp) / 65536
                
                # Chèn trực tiếp vào layout_box (role=1 là ô vuông đáp án)
                cursor.execute("""
                    INSERT OR IGNORE INTO layout_box 
                    (student, page, role, question, answer, xmin, xmax, ymin, ymax) 
                    VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)
                """, (int(std), int(pg), int(q_idx), int(ans), 
                      x_val-5, x_val+5, y_val-5, y_val+5))

    conn.commit()
    final_count = cursor.execute("SELECT count(*) FROM layout_box").fetchone()[0]
    conn.close()
    
    print(f"Tự động hóa xong! Tổng số ô vuông: {final_count}")
    return final_count > 0
