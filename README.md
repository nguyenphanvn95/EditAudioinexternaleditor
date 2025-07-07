# 🎧 Edit Audios in External Editor

## 📌 Giới thiệu

Add-on này cho phép bạn **mở và chỉnh sửa các file âm thanh** gắn trong thẻ Anki bằng phần mềm bên ngoài như **Audacity**. Bạn có thể cấu hình để chọn những âm thanh nào sẽ được mở dựa trên:
- Tên trường chứa âm thanh
- Vị trí âm thanh trên mặt trước hoặc mặt sau thẻ
- Regex (biểu thức chính quy) để tìm audio trong HTML

## ⚙️ Tính năng chính

- Mở một hoặc nhiều file audio liên kết với thẻ đang ôn luyện.
- Hỗ trợ 3 kiểu cấu hình tìm kiếm:
  - **Theo tên trường:** `Front,Back`
  - **Theo vị trí:** `1,2:1` → mở audio thứ 1, 2 ở mặt trước và audio thứ 1 ở mặt sau
  - **Theo biểu thức chính quy:** ví dụ `"<div id=\"editable\">.*?</div>"` (kết hợp checkbox "By regex")
- Cho phép thay đổi đường dẫn đến phần mềm chỉnh sửa audio.
- Giao diện cấu hình trực quan: chọn bộ thẻ, trường dữ liệu, và định dạng tìm kiếm.
- Tùy chọn lưu cấu hình theo từng bộ thẻ (deck).

## 🧭 Cách sử dụng

- Mở Anki → Menu **Tools** → **Edit audios in editor**
- Sử dụng phím tắt:
  - `Alt + G`: Mở audio trong thẻ đang xem
  - `Shift + G`: Mở cửa sổ cấu hình

### 3. Thiết lập cấu hình
- Chọn bộ thẻ (Deck)
- Nhập tiêu chí tìm kiếm (tên trường, chỉ số hoặc regex)
- Đổi phần mềm chỉnh sửa nếu cần
- (Tùy chọn) Tick "Save config" để lưu lại

## 🧪 Ví dụ

| Đầu vào tìm kiếm | Ý nghĩa |
|------------------|--------|
| `Front,Back`     | Mở âm thanh trong trường "Front" và "Back" |
| `1:2`            | Mở audio đầu tiên ở mặt trước, thứ hai ở mặt sau |
| `<div id="editable">.*?</div>` (tích regex) | Mở audio trong thẻ HTML cụ thể |

## 💻 Yêu cầu

- Anki >= 2.1.x
- Python 3.9+
- Đã cài sẵn phần mềm chỉnh sửa audio (Audacity hoặc phần mềm bất kỳ)

## 🛠 Đường dẫn mặc định editor

| Hệ điều hành | Mặc định |
|-------------|----------|
| Windows      | `C:\\Program Files (x86)\\Audacity\\audacity.exe` |
| macOS        | `/Applications/Audacity.app` |

Bạn có thể thay đổi thủ công qua nút "Change editor path" trong cấu hình.

## 📝 Ghi chú

- Chỉ hoạt động khi bạn đang **ở chế độ ôn tập thẻ (review mode)**.
- Addon có thể lỗi nếu đường dẫn audio bị sai hoặc editor không được tìm thấy.

## 📬 Tác giả & Đóng góp

- Tác giả gốc: https://ankiweb.net/shared/info/1502086928
- Chỉnh sửa & đóng gói lại: Nguyễn Văn Phán
