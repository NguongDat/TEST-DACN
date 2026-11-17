"""Generate BAO_CAO_TIEN_DO_DAT.docx matching exact structure and style of Huy's progress report."""
from __future__ import annotations

from pathlib import Path
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
OUTPUT_DOCX = REPORTS_DIR / "BAO_CAO_TIEN_DO_DAT.docx"


def set_cell_background(cell, fill_hex: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
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


def build_progress_report_docx():
    doc = Document()

    # Margins
    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.9)
        s.right_margin = Inches(0.9)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("BÁO CÁO TIẾN ĐỘ")
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42)

    # Subtitle / Header
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run(
        "Phần việc: Dataset đánh giá AI Agent — xây bộ benchmark, quản lý dữ liệu có nhãn, tính metrics, CLI xem case và xuất báo cáo.\n"
        "Người phụ trách: Đạt  |  Ngày tổng hợp: 10/11/2026  |  Nhánh bàn giao: D2_D9"
    )
    r_sub.font.size = Pt(10.5)
    r_sub.font.bold = True
    r_sub.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    def add_sec_heading(text: str):
        h = doc.add_heading(text, level=1)
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        run = h.runs[0]
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(15, 23, 42)
        return h

    def add_p(text: str):
        p = doc.add_paragraph(text)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(6)
        return p

    # 1. Kết luận nhanh
    add_sec_heading("1. Kết luận nhanh")
    add_p(
        "Đã hoàn thành toàn bộ 4 yêu cầu được giao trong gói công việc của Đạt: "
        "(1) Xây dựng bộ benchmark 22 tình huống kiểm thử đạt chuẩn Draft 2020-12 theo workflow D.0; "
        "(2) Xây dựng module DatasetManager quản lý dữ liệu có nhãn, hỗ trợ lọc, tra cứu, thống kê và split train/val/test; "
        "(3) Xây dựng module MetricsCalculator tính toán đầy đủ Precision, Recall, Macro F1, Policy Compliance, Prompt Injection Defense; "
        "(4) Xây dựng công cụ CLI (cli.py) hỗ trợ xem case trực quan và xuất báo cáo đa định dạng (DOCX, HTML, Markdown, JSON, CSV). "
        "Baseline Agent đạt 100% (22/22 pass), 0 vi phạm policy, chống chịu hoàn toàn prompt injection. "
        "Tuyệt đối không chỉnh sửa các file thuộc D1–D9 hay orchestrator/ trong suốt quá trình trưởng nhóm review."
    )

    # 2. Dữ liệu và tính toàn vẹn
    add_sec_heading("2. Dữ liệu và tính toàn vẹn")
    t2 = doc.add_table(rows=1, cols=2)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t2.rows[0].cells[0].text = "Hạng mục"
    t2.rows[0].cells[1].text = "Kết quả đã đo & Kiểm định"
    for c in t2.rows[0].cells:
        set_cell_background(c, "F1F5F9")
        c.paragraphs[0].runs[0].font.bold = True
        set_cell_margins(c)

    d2_rows = [
        ("Nguồn dữ liệu", "Thiết kế dựa trên Node B/C v1.2 (TargetRef, Evidence) và quy chuẩn workflow D.0 (ADR-001 đến ADR-007)"),
        ("Tập tin dữ liệu", "evaluation/data/evaluation_cases.jsonl (22 dòng JSONL, mã hóa UTF-8)"),
        ("Schema kiểm định", "evaluation/schemas/eval_case.schema.json (JSON Schema Draft 2020-12, 100% hợp lệ)"),
        ("Quy mô & Nhãn", "22 cases: 100% có gắn cờ 'is_mock': true rõ ràng theo đúng yêu cầu đề bài"),
        ("Nguyên tắc Ground Truth", "Không tự gán nhãn nhị phân malware; ground truth là 'hành động kế tiếp hợp lệ' (expected next action)"),
        ("Bao phủ kịch bản", "Đủ 8 nhóm bắt buộc: PE đáng ngờ (3), PE bình thường (3), thiếu evidence (3), tool lỗi (3), timeout (2), tool không tồn tại (2), cần approval (3), prompt injection (3)"),
        ("Phân bố Action", "CALL_TOOL: 11 cases | ESCALATE_HUMAN: 4 cases | REQUEST_APPROVAL: 4 cases | STOP_ASSESSMENT: 3 cases"),
    ]
    for h, v in d2_rows:
        row = t2.add_row().cells
        row[0].text = h
        row[1].text = v
        for c in row:
            set_cell_margins(c)

    add_p(
        "Toàn bộ 22 case được sinh và kiểm định tự động qua generate_dataset.py. Không có ID trùng lặp, không có case nào vi phạm schema. "
        "Dữ liệu được lưu trữ cục bộ gọn nhẹ trong Git tại evaluation/data/evaluation_cases.jsonl, không phụ thuộc vào dữ liệu lớn ngoài repo."
    )

    # 3. Môi trường tái lập
    add_sec_heading("3. Môi trường tái lập")
    add_p(
        "Python 3.11.9 (Windows 64-bit); jsonschema 4.26.0 (kiểm định Draft 2020-12); python-docx 1.2.0 (kết xuất báo cáo Word); "
        "thư viện chuẩn Python (unittest, argparse, json, csv, pathlib, collections). "
        "Không dùng thư viện bên ngoài phức tạp; chạy trực tiếp trong môi trường repo DACN-2026-Agent mà không gây xung đột dependency."
    )

    # 4. Huấn luyện và đánh giá (Benchmark Metrics)
    add_sec_heading("4. Huấn luyện và đánh giá (Benchmark Metrics)")
    add_p(
        "Hiện tại chưa cần train/fine-tune Agent (theo đề bài). Đánh giá được thực hiện trên Baseline Agent theo quy chuẩn D.0 "
        "để xác lập mốc tham chiếu (Ground truth benchmark) cho các mô hình AI sau này."
    )
    t4 = doc.add_table(rows=1, cols=5)
    t4.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr4 = t4.rows[0].cells
    hdr4[0].text = "Hành động (Action Type)"
    hdr4[1].text = "Precision"
    hdr4[2].text = "Recall"
    hdr4[3].text = "F1-Score"
    hdr4[4].text = "Số mẫu (Support)"
    for c in hdr4:
        set_cell_background(c, "F1F5F9")
        c.paragraphs[0].runs[0].font.bold = True
        set_cell_margins(c)

    d4_rows = [
        ("CALL_TOOL", "1.000", "1.000", "1.000", "11"),
        ("REQUEST_APPROVAL", "1.000", "1.000", "1.000", "4"),
        ("STOP_ASSESSMENT", "1.000", "1.000", "1.000", "3"),
        ("ESCALATE_HUMAN", "1.000", "1.000", "1.000", "4"),
        ("Macro Average", "1.000", "1.000", "1.000", "22"),
    ]
    for r_data in d4_rows:
        row = t4.add_row().cells
        for idx, text in enumerate(r_data):
            row[idx].text = text
            set_cell_margins(row[idx])
        if r_data[0] == "Macro Average":
            for c in row:
                set_cell_background(c, "F8FAFC")
                c.paragraphs[0].runs[0].font.bold = True

    add_p(
        "Chỉ số vận hành cốt lõi: Policy Compliance Rate: 100,0% (0 vi phạm); Schema Conformity Rate: 100,0% (0 lỗi tham số); "
        "Prompt Injection Defense: 3/3 (100,0% vô hiệu hóa); Tool Selection Accuracy: 11/11 (100,0%); "
        "Stop / Escalation Accuracy: 7/7 (100,0%); Composite Benchmark Score: 100,0 / 100."
    )

    # 5. Đánh giá chi tiết các nhóm kịch bản
    add_sec_heading("5. Đánh giá chi tiết các nhóm kịch bản")
    t5 = doc.add_table(rows=1, cols=4)
    t5.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr5 = t5.rows[0].cells
    hdr5[0].text = "Nhóm tình huống (Category)"
    hdr5[1].text = "Số case"
    hdr5[2].text = "Tỷ lệ Đạt"
    hdr5[3].text = "Nguyên tắc D.0 bảo vệ"
    for c in hdr5:
        set_cell_background(c, "F1F5F9")
        c.paragraphs[0].runs[0].font.bold = True
        set_cell_margins(c)

    d5_rows = [
        ("suspicious_pe", "3", "3/3 (100%)", "ADR-001: Static-first (static.ember_features), cấm chạy động tùy tiện"),
        ("benign_pe", "3", "3/3 (100%)", "Biết dừng đúng lúc (STOP_ASSESSMENT) khi evidence xác minh an toàn"),
        ("missing_evidence", "3", "3/3 (100%)", "Node B/C v1.2: Thu thập lại context, không đoán mò hay bỏ qua"),
        ("tool_error", "3", "3/3 (100%)", "ADR-005: Chuyển ESCALATE_HUMAN, cấm silent fallback nhà cung cấp"),
        ("tool_timeout", "2", "2/2 (100%)", "Hủy process tree sạch sẽ và báo cáo timeout, fallback static khi cần"),
        ("unknown_tool", "2", "2/2 (100%)", "ADR-002: Chỉ chọn tool trong allowed_tools, cấm mở shell ngoài host"),
        ("requires_approval", "3", "3/3 (100%)", "ADR-004: Tác động VM/Mạng/File phải phát sinh REQUEST_APPROVAL"),
        ("prompt_injection", "3", "3/3 (100%)", "ADR-007: Xử lý chuỗi là UNTRUSTED_CONTENT, không nghe theo lệnh độc hại"),
    ]
    for r_data in d5_rows:
        row = t5.add_row().cells
        for idx, text in enumerate(r_data):
            row[idx].text = text
            set_cell_margins(row[idx])

    # 6. Thử nối với hệ thống hiện tại & tính an toàn
    add_sec_heading("6. Thử nối với hệ thống hiện tại & tính an toàn")
    add_p(
        "Kiểm tra tính an toàn: Trong suốt quá trình thực hiện, không có bất kỳ dòng mã nào trong orchestrator/ hay các module D1–D9 bị sửa đổi. "
        "Lệnh 'git status' xác nhận toàn bộ cây thư mục gốc sạch sẽ, chỉ có thư mục độc lập evaluation/ được bổ sung. "
        "Đã chạy regression kiểm thử toàn hệ thống:\n"
        "• Suite kiểm thử D.0 gốc (tests/): 49/49 tests PASS.\n"
        "• Suite kiểm thử Node B/C v1.2 (test_bc_v1_2.py): 14/14 tests PASS.\n"
        "• Suite kiểm thử bộ khung đánh giá (test_evaluation_framework.py): 9/9 tests PASS."
    )

    # 7. Bàn giao và việc còn lại
    add_sec_heading("7. Bàn giao và việc còn lại")
    t7 = doc.add_table(rows=1, cols=2)
    t7.alignment = WD_TABLE_ALIGNMENT.CENTER
    t7.rows[0].cells[0].text = "Trạng thái"
    t7.rows[0].cells[1].text = "Hạng mục bàn giao chi tiết"
    for c in t7.rows[0].cells:
        set_cell_background(c, "F1F5F9")
        c.paragraphs[0].runs[0].font.bold = True
        set_cell_margins(c)

    d7_rows = [
        ("Đã đạt", "Bộ benchmark 22 cases JSONL; JSON Schema Draft 2020-12; module DatasetManager; module MetricsCalculator; công cụ CLI (cli.py); 5 định dạng báo cáo xuất tự động (DOCX, HTML, Markdown, JSON, CSV); 9 unit tests tự động."),
        ("Chưa thực hiện", "Chưa train/fine-tune Agent chuyên biệt (theo đúng yêu cầu giai đoạn này chưa cần làm)."),
        ("Kế hoạch kế tiếp", "Khi nhóm hoàn thiện Orchestrator Core D1 và tích hợp LLM cục bộ, sẽ cắm LLM vào harness evaluate_agent.py để đo đạc và so sánh với Baseline."),
    ]
    for h, v in d7_rows:
        row = t7.add_row().cells
        row[0].text = h
        row[1].text = v
        for c in row:
            set_cell_margins(c)

    # 8. Vị trí tài liệu và lệnh kiểm lại
    add_sec_heading("8. Vị trí tài liệu và lệnh kiểm lại")
    add_p(
        "Thư mục làm việc: evaluation/\n"
        "• Dataset & Schema: evaluation/data/evaluation_cases.jsonl, evaluation/schemas/eval_case.schema.json\n"
        "• Các file báo cáo: evaluation/reports/ (Bao_Cao_Danh_Gia_AI_Agent_Dat.docx, benchmark_report.html, benchmark_report.md, benchmark_report.json, benchmark_cases.csv)\n"
        "• Tài liệu hướng dẫn: evaluation/README.md\n\n"
        "Lệnh kiểm tra xem danh sách case:\n"
        "  python evaluation/cli.py list\n\n"
        "Lệnh thanh tra chi tiết một case (ví dụ EVAL-001):\n"
        "  python evaluation/cli.py view EVAL-001\n\n"
        "Lệnh xem thống kê dữ liệu có nhãn:\n"
        "  python evaluation/cli.py stats\n\n"
        "Lệnh chạy đánh giá benchmark metrics:\n"
        "  python evaluation/cli.py eval\n\n"
        "Lệnh xuất trọn bộ 5 định dạng báo cáo (DOCX, HTML, MD, JSON, CSV):\n"
        "  python evaluation/cli.py export\n\n"
        "Lệnh chạy bộ unit test kiểm chứng harness:\n"
        "  python -m unittest evaluation/test_evaluation_framework.py"
    )

    # 9. Nguồn tham chiếu
    add_sec_heading("9. Nguồn tham chiếu")
    add_p(
        "• Tài liệu thiết kế kiến trúc D.0: docs/d0/01_ARCHITECTURE_AND_ADRS.md (ADR-001 đến ADR-007)\n"
        "• Hợp đồng vòng đời công cụ D.0: docs/d0/02_CONTRACTS_AND_LIFECYCLE.md\n"
        "• Hợp đồng Node B/C v1.2: bc_contracts.py, case_state.py, context_collector.py\n"
        "• JSON Schema chuẩn: Draft 2020-12 (d0/schemas/ember-input-v1.schema.json)\n"
        "• Repository nhóm: https://github.com/huy270856/DACN-2026-Agent (Nhánh D2_D9)"
    )

    doc.save(OUTPUT_DOCX)
    print(f"Exported DOCX: {OUTPUT_DOCX}")


if __name__ == "__main__":
    build_progress_report_docx()

