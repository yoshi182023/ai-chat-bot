from app import app

# Vercel 需要这个变量
handler = app

if __name__ == "__main__":
    app.run()
