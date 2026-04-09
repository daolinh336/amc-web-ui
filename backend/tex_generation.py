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

\AMCboxStyle{shape=square, size=2.8ex, color=black}

\begin{document}
\AMCrandomseed{1237893}
\setdefaultgroupmode{withoutreplacement}
\AMCsetFoot{\thepage}
'''

HEADER_2 = r'''
\onecopy{COPIES}{

%%% beginning of the test sheet header:

\noindent{\bf QCM \hfill TEST}

\vspace{5mm}

\noindent
\begin{minipage}{0.45\linewidth}
  \centering\large\bf Test Examination on TODAY'S DATE
\end{minipage}
\hfill
\begin{minipage}{0.5\linewidth}
  \namefield{\fbox{
     \begin{minipage}{\linewidth}
        Firstname and lastname:

        \vspace*{0.5cm}\dotfill
     \end{minipage}
  }}
\end{minipage}

\vspace{8mm}

\noindent {\bf Mã số sinh viên (MSSV):}
\vspace{3mm}

\AMCcode{mssv}{8}
\vspace{8mm}


% ==========================


\begin{center}\em
Duration : 10 minutes.
\end{center}
'''


TRAILER = r'''
}

\end{document}
'''

def create_answer(text: str, is_correct: bool):
    cmd = 'correctchoice' if is_correct else 'wrongchoice'
    return f"\\{cmd}{{{text}}}"

def parse_question_dict(questions: dict, index: int = 1) -> str:
    answers = '\n'.join([create_answer(a['answerText'], a['correct']) for a in questions['answers']])

    question_type = 'questionmult' if sum(1 for a in questions['answers'] if a['correct']) > 1 else 'question'
    clean_topic = "".join(filter(str.isalnum, questions.get('topic') or 'default'))

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
