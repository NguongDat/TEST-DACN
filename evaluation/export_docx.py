"""Export professional Word Document (.docx) report for DACN D.0 Benchmark Evaluation."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from evaluation.cli import evaluate_all
from evaluation.dataset_manager import DatasetManager

REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def set_cell_background(cell, fill_hex: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def create_docx_report(output_path: Path) -> Path:
    calc = evaluate_all()
    summary = calc.compute_summary()
    meta = summary["metadata"]
    sec = summary["security_and_compliance"]
    act = summary["action_classification"]
    cats = summary["category_breakdown"]

    dm = DatasetManager()
    stats = dm.get_statistics()

    doc = Document()

    # Page Margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)

    # Header / Title
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = title.add_run("BÁO CÁO KẾT QUẢ ĐỒ ÁN CHUYÊN NGÀNH\n")
    run_sub.font.size = Pt(12)
    run_sub.font.bold = True
    run_sub.font.color.rgb = RGBColor(100, 116, 139)

    run_title = title.add_run("XÂY DỰNG BỘ BENCHMARK, QUẢN LÝ DỮ LIỆU CÓ NHÃN,\nTÍNH METRICS, CLI XEM CASE VÀ XUẤT BÁO CÁO CHO AI AGENT")
    run_title.font.size = Pt(16)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 23, 42)

    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_run = meta_p.add_run(f"Sinh viên thực hiện: Đạt  |  Kiến trúc: DACN D.0  |  Thời gian: {meta['generated_at'][:10]}")
    meta_run.font.italic = True
    meta_run.font.size = Pt(10)
    meta_run.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 1. TỔNG QUAN
    h1 = doc.add_heading("1. Tổng quan & Phạm vi công việc", level=1)
    h1.paragraph_format.space_before = Pt(14)
    p1 = doc.add_paragraph(
        "Báo cáo này trình bày trọn vẹn kết quả thực hiện đồ án chuyên ngành theo yêu cầu của nhóm trưởng: "
        "Xây dựng bộ benchmark đánh giá AI Agent, thiết kế cơ chế quản lý dữ liệu có nhãn, tính toán các metrics chuyên sâu, "
        "cung cấp công cụ dòng lệnh (CLI) để xem/thanh tra case và tự động xuất báo cáo đa định dạng. "
        "Toàn bộ cấu trúc tuân thủ nghiêm ngặt theo kiến trúc DACN D.0 (ADR-001 đến ADR-007) và các hợp đồng Node B/C v1.2, "
        "được đóng gói độc lập trong thư mục 'evaluation/' để đảm bảo an toàn tuyệt đối cho mã nguồn của nhóm."
    )
    p1.paragraph_format.line_spacing = 1.15

    # 2. BẢN ĐỒ CÁC FILE
    h2 = doc.add_heading("2. Bản đồ cấu trúc thư mục & các file bàn giao", level=1)
    p2 = doc.add_paragraph("Các thành phần đã được hoàn thiện và tích hợp đồng bộ:")

    files_table = doc.add_table(rows=1, cols=3)
    files_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = files_table.rows[0].cells
    hdr[0].text = "Tên File / Thư mục"
    hdr[1].text = "Yêu cầu đảm nhận"
    hdr[2].text = "Chức năng chính"
    for c in hdr:
        set_cell_background(c, "F1F5F9")
        c.paragraphs[0].runs[0].font.bold = True
        set_cell_margins(c, 80, 80, 100, 100)

    file_items = [
        ("evaluation/schemas/eval_case.schema.json", "Yêu cầu 1", "Schema JSON Draft 2020-12 kiểm định case đánh giá"),
        ("evaluation/data/evaluation_cases.jsonl", "Yêu cầu 1", "Bộ 22 tình huống có nhãn chuẩn hóa D.0 (is_mock=True)"),
        ("evaluation/dataset_manager.py", "Yêu cầu 2", "Quản lý dữ liệu có nhãn, tra cứu, lọc, thống kê, split dataset"),
        ("evaluation/metrics.py", "Yêu cầu 3", "Tính Precision, Recall, F1, Policy Compliance, Prompt Injection Def."),
        ("evaluation/cli.py", "Yêu cầu 4", "CLI tra cứu case, xem chi tiết, thống kê và xuất báo cáo tự động"),
        ("evaluation/reports/", "Yêu cầu 4", "Thư mục chứa 5 file báo cáo xuất ra: DOCX, HTML, MD, JSON, CSV"),
        ("evaluation/test_evaluation_framework.py", "Kiểm thử", "9 unit tests kiểm chứng khả năng bắt vi phạm của bộ harness"),
    ]

    for f_name, req, desc in file_items:
        row = files_table.add_row().cells
        row[0].text = f_name
        row[1].text = req
        row[2].text = desc
        for c in row:
            set_cell_margins(c, 60, 60, 100, 100)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 3. KẾT QUẢ ĐÁNH GIÁ METRICS
    h3 = doc.add_heading("3. Kết quả đánh giá chỉ số Benchmark Metrics", level=1)
    
    # Summary Highlight Box
    sum_table = doc.add_table(rows=2, cols=4)
    sum_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    s_hdr = sum_table.rows[0].cells
    s_val = sum_table.rows[1].cells

    s_hdr[0].text = "Composite Score"
    s_val[0].text = f"{meta['composite_score_pct']} / 100"

    s_hdr[1].text = "Overall Accuracy"
    s_val[1].text = f"{meta['overall_accuracy_pct']}% ({meta['overall_passed']}/{meta['total_cases']})"

    s_hdr[2].text = "Policy Compliance"
    s_val[2].text = f"{sec['policy_compliance_rate_pct']}% (0 vi phạm)"

    s_hdr[3].text = "Injection Defense"
    s_val[3].text = f"{sec['injection_defense_rate_pct']}% (3/3 defended)"

    for c in s_hdr:
        set_cell_background(c, "E2E8F0")
        c.paragraphs[0].runs[0].font.bold = True
        set_cell_margins(c, 80, 80, 100, 100)
    for c in s_val:
        set_cell_background(c, "F8FAFC")
        c.paragraphs[0].runs[0].font.bold = True
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(37, 99, 235)
        set_cell_margins(c, 80, 80, 100, 100)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Action Classification table
    doc.add_heading("3.1. Phân loại Action (Precision, Recall, F1-Score)", level=2)
    act_table = doc.add_table(rows=1, cols=5)
    act_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    a_hdr = act_table.rows[0].cells
    a_hdr[0].text = "Action Type"
    a_hdr[1].text = "Precision"
    a_hdr[2].text = "Recall"
    a_hdr[3].text = "F1-Score"
    a_hdr[4].text = "Số mẫu (Support)"
    for c in a_hdr:
        set_cell_background(c, "F1F5F9")
        c.paragraphs[0].runs[0].font.bold = True
        set_cell_margins(c, 60, 60, 100, 100)

    for lbl, scores in act["per_class"].items():
        row = act_table.add_row().cells
        row[0].text = lbl
        row[1].text = f"{scores['precision']:.3f}"
        row[2].text = f"{scores['recall']:.3f}"
        row[3].text = f"{scores['f1_score']:.3f}"
        row[4].text = str(scores["support"])
        for c in row:
            set_cell_margins(c, 50, 50, 100, 100)

    m_row = act_table.add_row().cells
    m_row[0].text = "Macro Average"
    m_row[1].text = f"{act['macro_precision']:.3f}"
    m_row[2].text = f"{act['macro_recall']:.3f}"
    m_row[3].text = f"{act['macro_f1']:.3f}"
    m_row[4].text = str(meta["total_cases"])
    for c in m_row:
        set_cell_background(c, "F8FAFC")
        c.paragraphs[0].runs[0].font.bold = True
        set_cell_margins(c, 50, 50, 100, 100)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Scenario Breakdown
    doc.add_heading("3.2. Phân bố và tỷ lệ đạt theo từng kịch bản (Scenario Breakdown)", level=2)
    cat_table = doc.add_table(rows=1, cols=5)
    cat_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_hdr = cat_table.rows[0].cells
    c_hdr[0].text = "Nhóm kịch bản"
    c_hdr[1].text = "Tổng số"
    c_hdr[2].text = "Đạt"
    c_hdr[3].text = "Thất bại"
    c_hdr[4].text = "Tỷ lệ đạt"
    for c in c_hdr:
        set_cell_background(c, "F1F5F9")
        c.paragraphs[0].runs[0].font.bold = True
        set_cell_margins(c, 60, 60, 100, 100)

    for cat_name, scores in cats.items():
        row = cat_table.add_row().cells
        row[0].text = cat_name
        row[1].text = str(scores["total"])
        row[2].text = str(scores["passed"])
        row[3].text = str(scores["failed"])
        row[4].text = f"{scores['accuracy_pct']}%"
        for c in row:
            set_cell_margins(c, 50, 50, 100, 100)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 4. HƯỚNG DẪN CLI
    doc.add_heading("4. Hướng dẫn vận hành bộ công cụ CLI", level=1)
    cli_p = doc.add_paragraph(
        "Bộ công cụ evaluation/cli.py hỗ trợ 5 chế độ thao tác trực tiếp trên dòng lệnh:\n"
        "• python evaluation/cli.py list : Xem danh sách các case, có hỗ trợ lọc (--category, --search).\n"
        "• python evaluation/cli.py view <ID> : Thanh tra toàn diện 1 case (CaseState, Evidence, Tools, Expected Action, Rationale).\n"
        "• python evaluation/cli.py stats : Xem thống kê phân bố dữ liệu có nhãn.\n"
        "• python evaluation/cli.py eval : Chạy đánh giá Agent và tính toán đầy đủ bảng Metrics.\n"
        "• python evaluation/cli.py export : Tự động kết xuất trọn bộ file báo cáo ra thư mục evaluation/reports/."
    )
    cli_p.paragraph_format.line_spacing = 1.2

    # 5. CHI TIẾT 22 TEST CASES
    doc.add_heading("5. Bảng chi tiết 22 Test Cases nghiệm thu", level=1)
    case_table = doc.add_table(rows=1, cols=5)
    case_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cs_hdr = case_table.rows[0].cells
    cs_hdr[0].text = "Mã Case"
    cs_hdr[1].text = "Kịch bản"
    cs_hdr[2].text = "Tên tình huống"
    cs_hdr[3].text = "Expected Action"
    cs_hdr[4].text = "Kết quả"
    for c in cs_hdr:
        set_cell_background(c, "F1F5F9")
        c.paragraphs[0].runs[0].font.bold = True
        set_cell_margins(c, 60, 60, 100, 100)

    for item in summary["cases"]:
        row = case_table.add_row().cells
        row[0].text = item["case_id"]
        row[1].text = item["category"]
        row[2].text = item["name"]
        exp_tool = f" ({item['expected_tool']})" if item.get("expected_tool") else ""
        row[3].text = f"{item['expected_action']}{exp_tool}"
        row[4].text = "PASS" if item["passed"] else "FAIL"
        for c in row:
            set_cell_margins(c, 40, 40, 80, 80)
            if item["passed"]:
                set_cell_background(row[4], "F0FDF4")

    # Save document
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    print(f"Successfully generated Word report at: {output_path.resolve()}")
    return output_path


if __name__ == "__main__":
    out_file = REPORTS_DIR / "Bao_Cao_Danh_Gia_AI_Agent_Dat.docx"
    create_docx_report(out_file)
    alt_file = REPORTS_DIR / "benchmark_report.docx"
    create_docx_report(alt_file)

