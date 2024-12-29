import os
import shutil
import zipfile
import pdfplumber
import re

subjects = {
    "국어": "국어",
    "통합사회": "통합사회",
    "한국사": "한국사",
    "수학": "수학",
    "과학탐구실험": "과학탐구실험",
    "통합과학": "통합과학",
    "영어": "영어",
    "정보": "정보",
    "독서": "독서",
    "문학": "문학",
    "경제": "경제",
    "사회문화": "사회문화",
    "생활과 윤리": "생활과윤리",
    "윤리와 사상": "윤리와사상",
    "한국지리": "한국지리",
    "수학Ⅰ": ["수학Ⅰ", "수학1"],
    "수학Ⅱ": ["수학Ⅱ", "수학2"],
    "확률과 통계": "확률과통계",
    "물리학Ⅰ": ["물리학Ⅰ", "물리학1"],
    "생명과학Ⅰ": ["생명과학Ⅰ", "생명과학1"],
    "지구과학Ⅰ": ["지구과학Ⅰ", "지구과학1"],
    "화학Ⅰ": ["화학Ⅰ", "화학1"],
    "영어Ⅰ": ["영어Ⅰ", "영어1"],
    "영어Ⅱ": ["영어Ⅱ", "영어2"],
    "독일어Ⅰ": ["독일어Ⅰ", "독일어1", "독일어"],
    "일본어Ⅰ": ["일본어Ⅰ", "일본어1", "일본어"],
    "중국어Ⅰ": ["중국어Ⅰ", "중국어1", "중국어"],
    "언어와 매체": "언어와매체",
    "화법과 작문": "화법과작문",
    "경제": "경제",
    "세계사": "세계사",
    "세계지리": "세계지리",
    "정치와 법": "정치와법",
    "기하": "기하",
    "미적분": "미적분",
    "물리학Ⅱ": ["물리학Ⅱ", "물리학2"],
    "생명과학Ⅱ": ["생명과학Ⅱ", "생명과학2"],
    "지구과학Ⅱ": ["지구과학Ⅱ", "지구과학2"],
    "화학Ⅱ": ["화학Ⅱ", "화학2"],
    "영어 독해와 작문": "영어독해와작문",
    "심화 국어": "심화국어",
    "경제 수학": "경제수학",
    "고전과 윤리": "고전과윤리",
    "사회문제 탐구": "사회문제탐구",
    "융합 과학": "융합과학",
    "심화 영어Ⅰ": "심화영어Ⅰ",
    "심화영어독해Ⅰ": "심화영어독해Ⅰ"
}

def extract_zip(zip_path, target_folder):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_folder)
        return target_folder
    except Exception as e:
        print(f"ZIP 파일 추출 오류 {zip_path}: {e}")
        return None

def extract_pdf(pdf_text):
    pdf_text = pdf_text.replace('\x00', '').replace(' ', '')

    grade = None
    subject = None
    exam_type = None
    year = None
    semester = None

    year_match = re.search(r"(\d{4})학년도", pdf_text)
    if year_match:
        year = year_match.group(1)

    lines = pdf_text.split('\n')
    for line in lines:

        grade_subject_match = re.search(r"(\d+학년)\s*(\S+)", line)
        if grade_subject_match:
            grade = grade_subject_match.group(1)
            extracted_subject = grade_subject_match.group(2).replace(" ", "")

            for subject_name, variations in subjects.items():
                if isinstance(variations, list):
                    if any(variation in extracted_subject for variation in variations):
                        subject = subject_name
                        break
                else:
                    if variations in extracted_subject:
                        subject = subject_name
                        break

            if not subject:
                for suffix in ['Ⅰ', 'Ⅱ']:
                    modified_subject = extracted_subject + suffix
                    for subject_name, variations in subjects.items():
                        if isinstance(variations, list):
                            if any(variation in modified_subject for variation in variations):
                                subject = subject_name
                                break
                        else:
                            if variations in modified_subject:
                                subject = subject_name
                                break
                if subject:
                    break
        
        if grade and subject:
            break

    semester_match = re.search(r"(1학기|2학기|1 학기|2 학기)", pdf_text)
    if semester_match:
        semester = semester_match.group(0).replace(' ', '')

    exam_type_match = re.search(r"(중간고사|기말고사)", pdf_text)
    if exam_type_match:
        exam_type = exam_type_match.group(0)

    if grade and subject and exam_type and year and semester:
        return {
            'grade': grade,
            'subject': subject,
            'exam_type': exam_type,
            'year': year,
            'semester': semester
        }
    return None

def process_pdf(pdf_path, target_folder):
    try:
        print(f"PDF 처리 중: {pdf_path}")
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 2:
                first_page = pdf.pages[0]
                first_page_text = first_page.extract_text()

                if not first_page_text:
                    for page in pdf.pages[1:]:
                        first_page_text = page.extract_text()
                        if first_page_text:
                            break

                if first_page_text:
                    extracted_info = extract_pdf(first_page_text)
                    if extracted_info:
                        pdf.close()
                        rename_and_move_pdf(pdf_path, extracted_info, target_folder) 
                    else:
                        print(f"{pdf_path}에서 유효한 정보를 추출할 수 없습니다.")
                else:
                    print(f"{pdf_path}에서 텍스트를 찾을 수 없습니다. 이미지 기반 PDF일 수 있습니다.")
            else:
                print(f"{pdf_path}는 페이지가 3개 미만이므로 건너뜁니다.")
    except Exception as e:
        print(f"PDF 처리 오류: {pdf_path}: {e}")

def rename_and_move_pdf(pdf_path, extracted_info, base_folder):
    try:
        grade = extracted_info['grade']
        subject = extracted_info['subject']
        exam_type = extracted_info['exam_type']
        year = extracted_info['year']
        semester = extracted_info['semester']

        grade_folder = os.path.join(base_folder, grade)
        os.makedirs(grade_folder, exist_ok=True)

        subject_folder = os.path.join(grade_folder, subject)
        os.makedirs(subject_folder, exist_ok=True)

        new_filename = f"{year}학년도 {semester} {exam_type} {subject}.pdf"
        new_pdf_path = os.path.join(subject_folder, new_filename)

        os.replace(pdf_path, new_pdf_path)
        print(f"{pdf_path}를 {new_pdf_path}로 이동했습니다.")

    except Exception as e:
        print(f"파일 이름 변경 및 이동 오류 {pdf_path}: {e}")

def process_files_in_directory(directory, target_folder):
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if file.lower().endswith('.zip'):
            extracted_folder = extract_zip(file_path, temp_folder)
            if extracted_folder:
                process_files_in_directory(extracted_folder, target_folder)
        elif file.lower().endswith('.pdf'):
            process_pdf(file_path, target_folder)

temp_folder = 'temp_pdfs'
pdf_directory = 'target'
classified_folder = 'classified'

try:
    shutil.rmtree(classified_folder)
    shutil.rmtree(temp_folder)
except FileNotFoundError:
    pass

process_files_in_directory(pdf_directory, classified_folder)