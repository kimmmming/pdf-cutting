from app import app

# Vercel needs the app to be named 'app' for serverless functions
if __name__ == "__main__":
    app.run()