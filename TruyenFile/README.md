# Hệ Thống Truyền File University 

Đây là một hệ thống demo cho phép giảng viên tải lên các tệp tài liệu, có tùy chọn mã hóa và ký số. Sinh viên có thể xem, tải xuống các tệp này và xác thực chữ ký số. Hệ thống sử dụng WebSocket để giao tiếp giữa client (trình duyệt) và server (Python).

## Tính năng chính

* Tải tệp lên: Giảng viên có thể tải lên các tệp tài liệu.
* Mã hóa tệp: Sử dụng AES-256 để mã hóa nội dung tệp trên client trước khi gửi lên server.
* Ký số tệp: Sử dụng RSA/SHA-256 để ký số tệp, đảm bảo tính toàn vẹn và xác thực nguồn gốc.
* Quản lý lớp học: Giảng viên có thể thêm và xem danh sách các lớp học.
* Lịch sử gửi: Giảng viên có thể xem lại các tệp đã tải lên.
* Quản lý khóa (Giảng viên): Giảng viên có thể tạo và xem cặp khóa RSA (công khai/riêng tư). Khóa riêng tư được sử dụng để ký số.
* Xem và Tải xuống tài liệu (Sinh viên): Sinh viên có thể xem danh sách các tệp được tải lên và tải chúng xuống.
* Giải mã tệp (Sinh viên): Tệp mã hóa sẽ tự động được giải mã khi tải xuống (với khóa AES được server cung cấp cho mục đích demo).
* Xác thực chữ ký (Sinh viên): Sinh viên có thể xác thực chữ ký số của tệp bằng cách sử dụng khóa công khai của giảng viên.
* Quản lý khóa cá nhân (Sinh viên): Sinh viên có thể tạo cặp khóa RSA cá nhân cho mục đích sử dụng sau này (ví dụ: ký nộp bài tập).

## Cấu trúc dự án

Tuyệt vời! Dựa trên cấu trúc dự án đã thống nhất, tôi sẽ tạo nội dung cho các tệp bạn yêu cầu: launch.json, settings.json, README.md, và requirements.txt.

Bạn cần tự tạo các thư mục rỗng như sau: files/, keys/, và .vscode/.

1. files/ (Thư mục)
Bạn chỉ cần tạo một thư mục trống tên là files ở cùng cấp với server.py.
Đây là nơi server sẽ lưu trữ các tệp đã tải lên.

2. keys/ (Thư mục)
Bạn chỉ cần tạo một thư mục trống tên là keys ở cùng cấp với server.py.
Đây là nơi server sẽ lưu trữ khóa công khai và khóa riêng của giảng viên dưới dạng tệp .pem để duy trì giữa các lần chạy.

3. .vscode/launch.json
Tệp này cấu hình cách VS Code khởi chạy (và gỡ lỗi) ứng dụng Python của bạn.

Tạo tệp: secure_file_transfer/.vscode/launch.json

JSON

{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Run Server",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/server.py",
            "console": "integratedTerminal",
            "justMyCode": true,
            "cwd": "${workspaceFolder}" // Đảm bảo chạy từ thư mục gốc của dự án
        }
    ]
}
Giải thích:

"name": "Python: Run Server": Tên hiển thị trong menu Debug của VS Code.

"type": "python": Cho biết đây là cấu hình chạy Python.

"request": "launch": Yêu cầu VS Code khởi chạy một chương trình.

"program": "${workspaceFolder}/server.py": Chỉ định tệp Python cần chạy. ${workspaceFolder} là một biến tích hợp của VS Code, đại diện cho thư mục gốc của dự án.

"console": "integratedTerminal": Kết quả đầu ra của chương trình sẽ hiển thị trong Terminal tích hợp của VS Code.

"justMyCode": true: Khi gỡ lỗi, chỉ dừng ở các breakpoint trong code của bạn, bỏ qua các thư viện bên thứ ba.

"cwd": "${workspaceFolder}": Đặt thư mục làm việc hiện tại cho chương trình là thư mục gốc của dự án. Điều này quan trọng để server.py có thể tìm thấy thư mục files và keys một cách chính xác.

4. .vscode/settings.json
Tệp này chứa các cài đặt cụ thể cho workspace (dự án) này, ghi đè lên các cài đặt người dùng chung nếu có. Điều này hữu ích để duy trì sự nhất quán giữa các nhà phát triển hoặc để thiết lập các quy tắc linter/formatter riêng cho dự án.

Tạo tệp: secure_file_transfer/.vscode/settings.json

JSON

{
    // Cài đặt cho Python extension
    "python.pythonPath": "${workspaceFolder}/venv/Scripts/python", // Windows
    // "python.pythonPath": "${workspaceFolder}/venv/bin/python", // macOS/Linux
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": [
        "--line-length",
        "120"
    ],
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.python", // Đảm bảo sử dụng Python formatter mặc định

    // Cài đặt cho HTML/JavaScript
    "editor.tabSize": 4, // Đảm bảo tab size nhất quán
    "files.associations": {
        "*.html": "html"
    },
    "emmet.includeLanguages": {
        "javascript": "html" // Cho phép Emmet trong JS khi dùng template literals
    },

    // Loại trừ một số thư mục khỏi tìm kiếm và cây thư mục
    "files.exclude": {
        "**/.git": true,
        "**/.svn": true,
        "**/.hg": true,
        "**/CVS": true,
        "**/.DS_Store": true,
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/venv": true // Ẩn thư mục môi trường ảo
    },
    "search.exclude": {
        "**/venv": true,
        "**/node_modules": true // Nếu có dự án Node.js sau này
    }
}
Lưu ý quan trọng về python.pythonPath:

Bạn cần uncomment dòng phù hợp với hệ điều hành của mình (Windows hoặc macOS/Linux) và comment/xóa dòng còn lại.

"${workspaceFolder}/venv/Scripts/python" là đường dẫn đến trình thông dịch Python trong môi trường ảo của bạn trên Windows.

"${workspaceFolder}/venv/bin/python" là đường dẫn tương tự trên macOS/Linux.

VS Code thường tự động phát hiện môi trường ảo khi bạn tạo nó, nhưng việc thiết lập rõ ràng trong settings.json đảm bảo nó luôn chọn đúng interpreter cho dự án này.

5. README.md
Tệp này là tài liệu quan trọng cho dự án của bạn, giúp người khác (hoặc chính bạn trong tương lai) hiểu cách thiết lập và chạy ứng dụng.

Tạo tệp: secure_file_transfer/README.md

Markdown

# Hệ Thống Chuyển Tệp Giáo Dục An Toàn (Secure Educational File Transfer System)

Đây là một hệ thống demo cho phép giảng viên tải lên các tệp tài liệu, có tùy chọn mã hóa và ký số. Sinh viên có thể xem, tải xuống các tệp này và xác thực chữ ký số. Hệ thống sử dụng WebSocket để giao tiếp giữa client (trình duyệt) và server (Python).

## Tính năng chính

* **Tải tệp lên**: Giảng viên có thể tải lên các tệp tài liệu.
* **Mã hóa tệp**: Sử dụng AES-256 để mã hóa nội dung tệp trên client trước khi gửi lên server.
* **Ký số tệp**: Sử dụng RSA/SHA-256 để ký số tệp, đảm bảo tính toàn vẹn và xác thực nguồn gốc.
* **Quản lý lớp học**: Giảng viên có thể thêm và xem danh sách các lớp học.
* **Lịch sử gửi**: Giảng viên có thể xem lại các tệp đã tải lên.
* **Quản lý khóa (Giảng viên)**: Giảng viên có thể tạo và xem cặp khóa RSA (công khai/riêng tư). Khóa riêng tư được sử dụng để ký số.
* **Xem và Tải xuống tài liệu (Sinh viên)**: Sinh viên có thể xem danh sách các tệp được tải lên và tải chúng xuống.
* **Giải mã tệp (Sinh viên)**: Tệp mã hóa sẽ tự động được giải mã khi tải xuống (với khóa AES được server cung cấp cho mục đích demo).
* **Xác thực chữ ký (Sinh viên)**: Sinh viên có thể xác thực chữ ký số của tệp bằng cách sử dụng khóa công khai của giảng viên.
* **Quản lý khóa cá nhân (Sinh viên)**: Sinh viên có thể tạo cặp khóa RSA cá nhân cho mục đích sử dụng sau này (ví dụ: ký nộp bài tập).

## Cấu trúc dự án

Truyen File University/
├── server.py             # Mã nguồn máy chủ Python WebSocket
├── client/
│   └── index.html        # Giao diện người dùng (HTML/CSS/JavaScript)
├── files/                # Thư mục lưu trữ các tệp đã tải lên
├── keys/                 # Thư mục lưu trữ khóa RSA của giảng viên
├── .vscode/
│   ├── launch.json       # Cấu hình khởi chạy và gỡ lỗi VS Code
│   └── settings.json     # Cài đặt workspace VS Code
├── README.md             # Tài liệu dự án
└── requirements.txt      # Danh sách các thư viện Python cần cài đặt

