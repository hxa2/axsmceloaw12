# Bài Toán Vận Tải – Transportation Problem Solver

Ứng dụng web giải bài toán vận tải với:
- **Phương pháp khởi tạo**: Cực tiểu chi phí (Least Cost), Góc Tây Bắc (Northwest Corner)  
- **Phương pháp tối ưu**: Thế vị (MODI/Potential Method)
- **Hiển thị**: Chi tiết từng bước, thế vị u/v, ma trận ước lượng Δ, chu trình điều chỉnh

## Cấu trúc dự án

```
.
├── backend/                  # FastAPI Python backend
│   ├── app/                  # Application layer (FastAPI, schemas, services)
│   │   ├── api/              # API routers (thin layer)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic orchestration
│   │   └── repositories/     # File I/O (Excel, CSV, JSON)
│   ├── core/                 # Pure Python algorithms (no framework)
│   │   ├── algorithms/       # Initial + optimization algorithms
│   │   ├── models/           # Domain models
│   │   └── validation/       # Input validation
│   └── tests/                # Unit + integration tests
├── frontend/                 # React + TypeScript + Vite frontend
│   └── src/
│       ├── api/              # API client
│       ├── components/       # UI components
│       ├── hooks/            # React hooks
│       ├── types/            # TypeScript types
│       └── utils/            # Utility functions
├── data/                     # Sample data files
│   ├── input/                # Input Excel/CSV files
│   └── output/               # Generated outputs
└── legacy/                   # Codebase cũ (CustomTkinter)
```

## Yêu cầu hệ thống (Requirements)

Để chạy dự án, máy tính của bạn cần cài đặt sẵn:
- **Python**: Phiên bản 3.10 trở lên (khuyến nghị 3.11+).
- **Node.js**: Phiên bản 20.0 trở lên (khuyến nghị 20.11+).
- **npm** hoặc **yarn** (đi kèm Node.js).
- Trình duyệt web hiện đại (Chrome, Edge, Firefox, Safari).

## Khởi động nhanh

### Backend (FastAPI)

```bash
cd backend

# Tạo virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# hoặc: .venv\Scripts\activate  # Windows

# Cài thư viện
pip install -r requirements.txt

# Chạy server
python -m uvicorn backend.app.main:app --reload
# API sẽ chạy tại: http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### Frontend (React)

```bash
cd frontend

# Cài thư viện (đã cài sẵn nếu làm theo thiết lập ban đầu)
npm install

# Chạy dev server
npm run dev
# Frontend sẽ chạy tại: http://localhost:5173
```

### Chạy tests

```bash
# Unit + integration tests
cd backend
python -m pytest -v

# Hoặc chỉ test algorithms
python -m pytest backend/tests/test_algorithms/ -v
```

## Kiến trúc

### Dependency flow (chỉ theo một chiều)
```
frontend → backend/app (FastAPI) → backend/core (thuần Python)
```

### Core algorithms (không phụ thuộc framework)
- `backend/core/algorithms/initial_solution/least_cost.py`: Cực tiểu chi phí
- `backend/core/algorithms/initial_solution/northwest_corner.py`: Góc Tây Bắc
- `backend/core/algorithms/optimization/potential_method.py`: Thế vị (MODI)

### API endpoints
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/transportation/health` | Health check |
| GET | `/api/transportation/methods` | Danh sách thuật toán |
| GET | `/api/transportation/samples` | Bài toán mẫu |
| POST | `/api/transportation/solve` | Giải từ JSON |
| POST | `/api/transportation/solve-from-file` | Giải từ file |

## Định dạng file tải lên

Hệ thống hỗ trợ 4 loại file đầu vào: `.xlsx`, `.xls`, `.csv`, và `.json`.

### 1. File Excel (.xlsx, .xls)
File Excel phải có đúng **3 sheet** theo thứ tự:
- **Sheet 1 (Index 0)**: Ma trận cước phí C (kích thước m × n), thuần số.
- **Sheet 2 (Index 1)**: Vectơ lượng phát (Supply) A (1 hàng hoặc 1 cột).
- **Sheet 3 (Index 2)**: Vectơ lượng thu (Demand) B (1 hàng hoặc 1 cột).

### 2. File CSV (.csv)
File CSV cần có các từ khóa `cost_matrix`, `supply`, và `demand` để phân tách các khối dữ liệu:
- Dòng chứa từ khóa `cost_matrix`
- Các dòng tiếp theo: các hàng của ma trận cước phí (ngăn cách bằng dấu phẩy)
- Dòng chứa từ khóa `supply`
- Dòng tiếp theo: giá trị lượng phát (ngăn cách bằng dấu phẩy)
- Dòng chứa từ khóa `demand`
- Dòng tiếp theo: giá trị lượng thu (ngăn cách bằng dấu phẩy)

### 3. File JSON (.json)
File JSON có cấu trúc đối tượng với các trường bắt buộc: `costMatrix`, `supply`, và `demand`. (Có thể thêm tùy chọn `sourceNames` và `destinationNames`).
```json
{
  "costMatrix": [
    [3, 1, 7, 4],
    [2, 6, 5, 9],
    [8, 3, 3, 2]
  ],
  "supply": [250, 350, 400],
  "demand": [200, 300, 350, 150]
}
```

## Hướng dẫn sử dụng

1. **Khởi tạo bài toán**: Tại màn hình chính, bạn có thể chỉnh sửa kích thước ma trận `m` (trạm phát) và `n` (trạm thu), sau đó điền trực tiếp cước phí, lượng phát và lượng thu vào các ô trống. Hoặc, bạn có thể tải lên một file Excel chứa dữ liệu theo format chuẩn hoặc chọn một "Bài mẫu" có sẵn.
2. **Chọn thuật toán khởi tạo**: Lựa chọn giữa phương pháp "Cực tiểu chi phí" hoặc "Góc Tây Bắc". Thuật toán tối ưu sẽ luôn là phương pháp Thế vị (MODI).
3. **Giải toán**: Nhấn nút **"Giải bài toán"**.
4. **Theo dõi quá trình giải**:
   - Sử dụng thanh điều khiển **"Các bước giải"** ở trên cùng để chuyển tiếp qua từng bước (hoặc ấn `Auto-run` để chạy tự động).
   - Bật/tắt các khung nhìn bằng cách nhấn vào **Giải thích, Ma trận, Mạng lưới, Biểu đồ** trên thanh công cụ để có cái nhìn trực quan và dễ hiểu nhất.
   - Nhấn nút **"Trình chiếu"** để tối ưu hóa không gian hiển thị, phù hợp cho việc giảng dạy và báo cáo trên máy chiếu.
   - Khi ở khung Ma trận, bạn có thể ấn **"Phóng to/Thu nhỏ/Vừa khít"** để xem rõ hơn đối với các bài toán kích thước lớn.
