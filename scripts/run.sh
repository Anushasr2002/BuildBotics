
#!/bin/bash
source venv/bin/activate
uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 &
cd frontend
npm start
