# DACN D.0 AI Agent Benchmark, Data Management & Metrics Suite

**Chịu trách nhiệm (Sinh viên):** Đạt  
**Phạm vi đề bài:**
> *"Xây bộ benchmark, quản lý dữ liệu có nhãn, tính metrics, CLI xem case và xuất báo cáo"*

**Cam kết an toàn mã nguồn:** Toàn bộ công việc nằm hoàn toàn độc lập trong thư mục `evaluation/`. Tuyệt đối không can thiệp, không sửa đổi bất kỳ file nào trong `orchestrator/`, `d0/` hoặc D1–D9 trong suốt quá trình nhóm trưởng đang review.

---

## 1. Bản đồ cấu trúc thư mục bàn giao

```
DACN-2026-Agent/evaluation/
├── schemas/
│   └── eval_case.schema.json         # [Yêu cầu 1] Schema JSON Draft 2020-12 kiểm định case evaluation
├── data/
│   └── evaluation_cases.jsonl        # [Yêu cầu 1] Bộ dataset 22 kịch bản có nhãn chuẩn hóa D.0
├── dataset_manager.py                # [Yêu cầu 2] Module quản lý dữ liệu có nhãn (Query, Filter, Stats, Split)
├── metrics.py                        # [Yêu cầu 3] Module tính metrics (F1, Precision, Recall, Policy, Security)
├── cli.py                            # [Yêu cầu 4] CLI xem case, thống kê dữ liệu và xuất báo cáo đa định dạng
├── evaluate_agent.py                 # Core harness chấm điểm AI Agent theo workflow D.0
├── generate_dataset.py               # Script tái tạo và kiểm định tính toàn vẹn dataset
├── test_evaluation_framework.py      # Bộ 9 unit tests kiểm chứng hệ thống đánh giá
└── reports/                          # [Yêu cầu 4] Thư mục chứa báo cáo xuất ra
    ├── benchmark_report.json         # Báo cáo chi tiết định dạng JSON
    ├── benchmark_report.md           # Báo cáo đánh giá định dạng Markdown
    ├── benchmark_report.html         # Dashboard báo cáo giao diện HTML trực quan
    └── benchmark_cases.csv           # Bảng tổng hợp quyết định từng case định dạng CSV
```

---

## 2. Bốn Trụ cột tính năng theo đúng đề bài

### Trụ cột 1: Xây bộ benchmark (22 cases bao phủ 8 kịch bản bắt buộc)
- Toàn bộ 22 cases được định dạng theo chuẩn JSON Lines và kiểm định nghiêm ngặt bởi `eval_case.schema.json`.
- Đánh dấu mock minh bạch: 100% case đều có `"is_mock": true`.
- Không tự gán nhãn malware bừa bãi làm ground truth; ground truth là hành động hợp lệ của workflow (`expected_action`) theo D.0 ADR-001 đến ADR-007:
  1. **PE đáng ngờ (`suspicious_pe`)**: 3 cases (`EVAL-001` -> `003`) - Tuân thủ nguyên tắc Static-first.
  2. **PE bình thường (`benign_pe`)**: 3 cases (`EVAL-004` -> `006`) - Dừng đúng lúc (`STOP_ASSESSMENT`).
  3. **Thiếu evidence (`missing_evidence`)**: 3 cases (`EVAL-007` -> `009`) - Yêu cầu thu thập lại context.
  4. **Tool lỗi (`tool_error`)**: 3 cases (`EVAL-010` -> `012`) - Báo lỗi `ESCALATE_HUMAN`, cấm silent fallback (ADR-005).
  5. **Timeout (`tool_timeout`)**: 2 cases (`EVAL-013` -> `014`) - Hủy process an toàn và chuyển hướng.
  6. **Tool không tồn tại/disabled (`unknown_tool`)**: 2 cases (`EVAL-015` -> `016`) - Chặn gọi ngoài `allowed_tools`.
  7. **Hành động cần approval (`requires_approval`)**: 3 cases (`EVAL-017` -> `019`) - Bắt buộc sinh `REQUEST_APPROVAL` (ADR-004).
  8. **Prompt injection (`prompt_injection`)**: 3 cases (`EVAL-020` -> `022`) - Coi nội dung là `UNTRUSTED_CONTENT` (ADR-007).

### Trụ cột 2: Quản lý dữ liệu có nhãn (`dataset_manager.py`)
Cung cấp class `DatasetManager`:
- Đọc/ghi và kiểm tra tính toàn vẹn (trùng lặp ID, thiếu trường bắt buộc).
- Lọc theo kịch bản (`category`), hành động (`action_type`), trạng thái mock (`is_mock`).
- Tìm kiếm từ khóa (`search`) xuyên suốt ID, tên, mô tả và lý do workflow.
- Tính toán thống kê dữ liệu: số lượng phân bố theo category, workflow phase, action type, evidence origin, trust level.
- Chia tập dữ liệu phân tầng (`split_dataset`: Train / Validation / Test).

### Trụ cột 3: Tính toán Metrics chuyên sâu (`metrics.py`)
Cung cấp class `MetricsCalculator`:
- **Độ chính xác phân loại Action:** Precision, Recall, F1-Score cho từng hành động (`CALL_TOOL`, `REQUEST_APPROVAL`, `STOP_ASSESSMENT`, `ESCALATE_HUMAN`) cùng Ma trận nhầm lẫn (Confusion Matrix).
- **Tỷ lệ tuân thủ Policy:** Tính tỷ lệ quyết định tuân thủ nghiêm ngặt `allowed_tools` (phát hiện `POLICY VIOLATION`).
- **Tỷ lệ hợp quy Schema:** Kiểm định đối chiếu tham số gọi tool với `ember-input-v1.schema.json` (phát hiện `SCHEMA ERROR`).
- **Khả năng phòng vệ Prompt Injection:** Tỷ lệ chống đỡ thành công các chuỗi chỉ thị độc hại cài cắm trong binary/log.
- **Biết dừng và chuyển tiếp an toàn:** Đo lường tính chuẩn xác khi kết luận an toàn hoặc chuyển giao chuyên gia (`ESCALATE_HUMAN`).
- **Composite Benchmark Score:** Chỉ số tổng hợp chuẩn hóa thang điểm 100.

### Trụ cột 4: CLI xem case và xuất báo cáo (`cli.py`)
Giao diện dòng lệnh thân thiện, không phụ thuộc thư viện ngoài:

```bash
# 1. Liệt kê danh sách các test cases (hỗ trợ lọc theo category, action, tìm kiếm)
python evaluation/cli.py list
python evaluation/cli.py list --category suspicious_pe
python evaluation/cli.py list --search entropy

# 2. Xem chi tiết thông tin 1 case cụ thể (CaseState, Evidence, Tools, Next Action, Rationale)
python evaluation/cli.py view EVAL-001

# 3. Xem thống kê dữ liệu có nhãn (phân bố category, phase, action, trust levels)
python evaluation/cli.py stats

# 4. Chạy đánh giá Agent và in bảng Metrics chi tiết (F1, Precision, Recall, Category Breakdown)
python evaluation/cli.py eval

# 5. Xuất báo cáo ra các định dạng file (JSON, Markdown, HTML, CSV)
python evaluation/cli.py export
python evaluation/cli.py export --formats json,md,html,csv --output evaluation/reports/
```

---

## 3. Kết quả thực tế khi chạy nghiệm thu

### 3.1. Chạy đánh giá Benchmark Metrics (`python evaluation/cli.py eval`)
```text
============================================================================
      DACN D.0 AGENT BENCHMARK EVALUATION METRICS REPORT
============================================================================
Overall Accuracy       : 100.0% (22/22)
Composite Score        : 100.0 / 100
Policy Compliance Rate : 100.0% (Violations: 0)
Schema Conformity Rate : 100.0% (Errors: 0)
Prompt Injection Def.  : 100.0% (Defended: 3)
Tool Selection Accuracy: 100.0%
Stop / Escalation Acc. : 100.0%
----------------------------------------------------------------------------
Action Classification Metrics:
+------------------+-----------+--------+----------+---------+
| Action Type      | Precision | Recall | F1-Score | Support |
+------------------+-----------+--------+----------+---------+
| CALL_TOOL        | 1.000     | 1.000  | 1.000    | 11      |
| REQUEST_APPROVAL | 1.000     | 1.000  | 1.000    | 4       |
| STOP_ASSESSMENT  | 1.000     | 1.000  | 1.000    | 3       |
| ESCALATE_HUMAN   | 1.000     | 1.000  | 1.000    | 4       |
| Macro Avg        | 1.000     | 1.000  | 1.000    | 22      |
+------------------+-----------+--------+----------+---------+
----------------------------------------------------------------------------
Category Breakdown:
+-------------------+-------+--------+--------+----------+
| Category          | Total | Passed | Failed | Accuracy |
+-------------------+-------+--------+--------+----------+
| benign_pe         | 3     | 3      | 0      | 100.0%   |
| missing_evidence  | 3     | 3      | 0      | 100.0%   |
| prompt_injection  | 3     | 3      | 0      | 100.0%   |
| requires_approval | 3     | 3      | 0      | 100.0%   |
| suspicious_pe     | 3     | 3      | 0      | 100.0%   |
| tool_error        | 3     | 3      | 0      | 100.0%   |
| tool_timeout      | 2     | 2      | 0      | 100.0%   |
| unknown_tool      | 2     | 2      | 0      | 100.0%   |
+-------------------+-------+--------+--------+----------+
============================================================================
```

### 3.2. Chạy xuất file báo cáo (`python evaluation/cli.py export`)
Đã xuất trọn bộ 4 file báo cáo vào thư mục `evaluation/reports/`:
- `benchmark_report.json`: Dữ liệu số liệu đầy đủ, ma trận nhầm lẫn và kết quả chi tiết từng case.
- `benchmark_report.md`: Báo cáo trình bày markdown chuẩn học thuật.
- `benchmark_report.html`: Dashboard trực quan có thẻ tóm tắt và bảng màu hiển thị tình trạng PASS/FAIL.
- `benchmark_cases.csv`: Bảng dữ liệu dạng bảng tính phục vụ tra cứu nhanh.

### 3.3. Chạy Unit Tests tự động (`python -m unittest evaluation/test_evaluation_framework.py`)
```text
.........
----------------------------------------------------------------------
Ran 9 tests in 0.008s

OK
```
9/9 test cases thành công, chứng minh hệ thống phát hiện chính xác: vi phạm policy, lỗi tham số sai schema, lỗ hổng prompt injection, thiếu lý do dừng case, lọc dữ liệu và tính toán metrics.
