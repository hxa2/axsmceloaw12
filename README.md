# Mô Phỏng Tối Ưu Hóa Bài Toán Vận Tải Bằng Thuật Toán Thế Vị

Chào mừng bạn đến với dự án **Mô phỏng & Tối ưu hóa Bài toán Vận tải**. Đây là một ứng dụng Python hoàn chỉnh bao gồm công cụ tính toán hiệu năng cao chạy trên giao diện dòng lệnh (CLI) và một giao diện người dùng đồ họa hiện đại (GUI) giúp trực quan hóa từng bước giải thuật toán thế vị một cách sinh động, trực quan và dễ tiếp cận.

---

## 1. Mô Tả Bài Toán Vận Tải (Transportation Problem)

**Bài toán vận tải** là một dạng bài toán Quy hoạch tuyến tính cổ điển, được ứng dụng rộng rãi trong tối ưu hóa chuỗi cung ứng và logistics. 

### Mục tiêu
Tìm phương án vận chuyển hàng hóa tối ưu từ **$m$ trạm phát** (nguồn cung) đến **$n$ trạm thu** (nhu cầu) sao cho **tổng chi phí vận chuyển là cực tiểu**.

### Mô hình Toán học

Cho trước:
*   Danh sách $m$ trạm phát $P_1, P_2, \dots, P_m$ với lượng trữ lượng phát tương ứng là $A = [a_1, a_2, \dots, a_m]$.
*   Danh sách $n$ trạm thu $T_1, T_2, \dots, T_n$ với lượng nhu cầu thu tương ứng là $B = [b_1, b_2, \dots, b_n]$.
*   Ma trận cước phí vận chuyển đơn vị $C_{m \times n} = [c_{ij}]$, trong đó $c_{ij}$ là chi phí vận chuyển một đơn vị hàng hóa từ trạm phát $i$ đến trạm thu $j$.

Giả thiết bài toán cân bằng thu phát (đóng):
$$\sum_{i=1}^{m} a_i = \sum_{j=1}^{n} b_j$$

Cần tìm ma trận phân bổ lượng hàng vận chuyển $X_{m \times n} = [x_{ij}]$ ($x_{ij} \ge 0$) sao cho:

$$\text{Cực tiểu hóa hàm mục tiêu: } f(X) = \sum_{i=1}^{m} \sum_{j=1}^{n} c_{ij} x_{ij} \longrightarrow \min$$

Dưới các ràng buộc:
1.  **Ràng buộc lượng phát:** $\sum_{j=1}^{n} x_{ij} = a_i \quad \forall i = 1, \dots, m$ (phát hết trữ lượng).
2.  **Ràng buộc lượng thu:** $\sum_{i=1}^{m} x_{ij} = b_j \quad \forall j = 1, \dots, n$ (thỏa mãn đầy đủ nhu cầu).
3.  **Điều kiện không âm:** $x_{ij} \ge 0 \quad \forall i, j$.

---

## 2. Các Thuật Toán Áp Dụng

Chương trình giải quyết bài toán vận tải qua **2 giai đoạn** cốt lõi:

### Giai đoạn 1: Tìm Phương Án Cực Biên Xuất Phát (Initial Feasible Solution)
Mục tiêu là tìm ra phương án ban đầu thỏa mãn các ràng buộc và có đúng $m + n - 1$ ô cơ sở, không chứa chu trình khép kín. Dự án hỗ trợ 2 thuật toán:
1.  **Phương pháp Cực tiểu Chi phí (Least Cost Method - LCM):** Ưu tiên phân phối hàng hóa vào các ô có cước phí rẻ nhất trên bảng nhằm đạt được chi phí xuất phát tối ưu hơn.
2.  **Phương pháp Góc Tây Bắc (Northwest Corner Method - NWC):** Bắt đầu phân bổ từ ô góc trên cùng bên trái $(1,1)$, đi dần xuống góc dưới bên phải theo lượng cung/cầu mà không xét đến giá trị cước phí.

> **Xử lý suy biến:** Khi cả lượng phát và lượng thu cùng bị triệt tiêu đồng thời ở một bước phân bổ, chương trình sẽ tự động kích hoạt thuật toán **bổ sung ô suy biến** ($x_{ij} = 0$ nhưng được tính là ô cơ sở) để đảm bảo luôn có đủ $m + n - 1$ ô độc lập tuyến tính, giúp giai đoạn 2 có thể giải được hệ thế vị.

---

### Giai đoạn 2: Tối Ưu Hóa Bằng Thuật Toán Thế Vị (Potential Method)
Thuật toán Thế vị (hay phương pháp hệ số $u-v$) kiểm tra tính tối ưu và cải thiện phương án theo các bước lặp sau:

1.  **Tính hệ thế vị:** Xác định các thế vị hàng $u_i$ ($i=1..m$) và thế vị cột $v_j$ ($j=1..n$) từ hệ phương trình tuyến tính đối với các ô cơ sở:
    $$u_i + v_j = c_{ij} \quad \forall (i, j) \in \text{Tập cơ sở}$$
    *(Hệ được giải bằng cách duyệt đồ thị BFS trên lưới cơ sở lưỡng phân, chọn mốc neo $u_1 = 0$)*.
2.  **Tính ma trận ước lượng kiểm tra tối ưu ($\Delta_{ij}$):** Đối với tất cả các ô loại (ô không thuộc tập cơ sở), tính chỉ số đánh giá:
    $$\Delta_{ij} = u_i + v_j - c_{ij}$$
3.  **Kiểm tra điều kiện tối ưu:**
    *   Nếu $\Delta_{ij} \le 0 \quad \forall (i, j) \notin \text{Tập cơ sở} \implies$ **Phương án đã đạt tối ưu toàn cục ($X^*$)**. Chương trình dừng thuật toán.
    *   Nếu tồn tại $\Delta_{ij} > 0 \implies$ Chưa tối ưu. Tiến hành chọn ô có $\Delta_{ij}$ dương lớn nhất để đưa vào làm ô cơ sở mới (gọi là **ô vào**).
4.  **Dựng chu trình điều chỉnh:** Tìm chu trình khép kín duy nhất đi qua ô vào và một số ô cơ sở hiện tại bằng giải thuật duyệt độ sâu **DFS**.
5.  **Điều chỉnh luồng hàng hóa:** Đánh dấu xen kẽ dấu $(+)$ tại ô vào, dấu $(-)$ tại ô cơ sở tiếp theo trên chu trình. Xác định lượng hàng điều chỉnh tối đa:
    $$\theta = \min \{ x_{ij} \mid (i, j) \in \text{Chu trình mang dấu } (-) \}$$
    Cộng $\theta$ vào các ô dấu $(+)$ và trừ $\theta$ ở các ô dấu $(-)$. Cập nhật tập cơ sở (ô đạt min $\theta$ dấu $(-)$ sẽ bị loại ra khỏi tập cơ sở, gọi là **ô ra**).
6.  **Lặp lại:** Trở lại bước 1 với tập cơ sở mới.

> **Chống vòng lặp vô hạn (Cycling Detection):** Trong các trường hợp suy biến nặng khi $\theta = 0$, chương trình sử dụng cấu trúc lưu vết `frozenset` tập cơ sở để phát hiện hiện tượng lặp chu kỳ tập cơ sở và cảnh báo kịp thời cho người dùng.

---

## 3. Cấu Trúc Mã Nguồn

```text
Bài toán vận tải/
├── requirements.txt                 # Danh sách thư viện phụ thuộc
├── logic/                           # Thư mục chứa các module logic tính toán
│   ├── data_loader.py               # Đọc ma trận và lượng cung/cầu từ file Excel
│   ├── generate_sample_data.py      # Tạo file Excel bài toán mẫu (Classic & Suy biến)
│   ├── initial_solution.py          # Thuật toán LCM, NWC & quản lý ô cơ sở BasisSet
│   ├── potential_method.py          # Giải thuật Thế vị (u-v), BFS thế vị, DFS chu trình, Pivot
│   └── visualizer.py                # Vẽ ma trận phân bổ xuất ra file PNG đẹp mắt
├── ui/                              # Thư mục chứa các giao diện chạy chương trình
│   ├── main.py                      # Điểm khởi chạy giao diện dòng lệnh (CLI Console)
│   └── ui.py                        # Giao diện đồ họa (GUI CustomTkinter) chuyên nghiệp
└── data_and_results/                # Thư mục chứa dữ liệu đầu vào và kết quả đầu ra
    ├── input_data.xlsx              # File Excel chứa dữ liệu bài toán đầu vào
    ├── optimization_log.txt         # Log chi tiết từng bước lặp, ma trận delta, chu trình
    └── solution_table.png           # Ảnh chụp bảng phân bổ tối ưu hóa cuối cùng
```

---

## 4. Hướng Dẫn Cài Đặt & Chạy Chương Trình (Giao Diện GUI)

### Cài đặt Hệ thống & Thư viện
1. Đảm bảo máy tính của bạn đã cài đặt **Python 3.9** trở lên.
2. Mở Terminal/PowerShell tại thư mục dự án và cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
   *(Các thư viện chính bao gồm: `customtkinter` cho giao diện GUI chuyên nghiệp, `pandas` & `openpyxl` để xử lý file Excel, `numpy` cho tính toán ma trận, và `matplotlib` để vẽ đồ thị)*

### Khởi chạy Giao diện (GUI)
Bạn có thể khởi động ứng dụng với giao diện đồ họa (GUI) bằng cách chạy lệnh sau. Hệ thống đã được cấu hình tự động nhận diện đường dẫn tuyệt đối, cho phép bạn đứng ở **bất kỳ thư mục nào** trong Terminal/PowerShell để chạy mà không cần di chuyển (`cd`) vào thư mục dự án:

```bash
# Nếu đang ở trong thư mục dự án:
python ui/ui.py

# Nếu đang ở bất kỳ thư mục nào khác (ví dụ: C:\Users\Admin):
python "C:\đường_dẫn_đến_folder\Bài toán vận tải\ui\ui.py"
```

### Các bước sử dụng nhanh trên GUI
* **Nhập dữ liệu:** Nhấn **Upload Excel** để chọn tệp dữ liệu của bạn, hoặc cấu hình kích thước nguồn phát ($m$) và nguồn thu ($n$) rồi nhấn **Tạo dữ liệu mẫu** (có tùy chọn tạo bài toán suy biến).
* **Giải bài toán:** Lựa chọn phương pháp tìm phương án ban đầu (LCM hoặc NWC) rồi nhấn nút **Giải bài toán**.
* **Xem kết quả:**
  * Bảng phân bổ tối ưu hóa hiển thị trực quan (ô cơ sở được làm nổi bật bằng màu xanh nhạt).
  * Đồ thị phân phối hiển thị trực quan trên giao diện và có thể lưu thành file ảnh.
  * Nhấn **Xem Nhật Ký** để theo dõi chi tiết từng bước lặp tính thế vị ($u_i, v_j$), ma trận $\Delta$ và chu trình điều chỉnh.

---

## 5. Định Dạng File Excel Đầu Vào
Nếu bạn upload tệp Excel tự tạo, tệp cần chứa chính xác **3 Sheet** chứa dữ liệu dạng số (không ghi nhãn hàng/cột):
1. **Sheet `Chi_phi`**: Chứa ma trận cước phí đơn vị $C$ ($m$ hàng, $n$ cột).
2. **Sheet `Luong_phat`**: Dòng đơn gồm $m$ cột chứa trữ lượng phát $A$.
3. **Sheet `Luong_thu`**: Dòng đơn gồm $n$ cột chứa nhu cầu thu $B$.

*(Bạn có thể tham khảo tệp tự sinh `data_and_results/input_data.xlsx` khi chạy tính năng tạo dữ liệu mẫu trên ứng dụng).*
