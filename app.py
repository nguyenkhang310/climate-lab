import os
from bang_dieu_khien.nguyen_khang.ung_dung import app

server = app.server

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=int(os.environ.get("PORT", 8050)))
