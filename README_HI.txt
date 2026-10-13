INSTAYT DOWNLOADER — BACKEND PROJECT

Is project me:
- Instagram public Reel/video download request
- Instagram video se audio (MP3/M4A)
- YouTube audio (MP3/M4A)
- Video quality option: 720p ya 1080p
- Download request ke baad input field clear hota hai
- Public profile downloader section nahi hai

LOCAL COMPUTER:
1. Python 3.11+ install karein.
2. FFmpeg install karke PATH me add karein (audio conversion ke liye).
3. Terminal/CMD me project folder kholein:
   pip install -r requirements.txt
   python app.py
4. Browser me http://127.0.0.1:5000 kholein.

ONLINE HOSTING:
- Project ko GitHub repository me upload karein.
- Render par New Web Service -> repository select karein.
- render.yaml settings use karein, ya build command:
  pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg
- start command: gunicorn app:app
- Deployment ke baad Render URL open karein.

IMPORTANT:
- Ye app sirf public, accessible links ke liye hai; private/login-protected content
  ko access karne ki koshish nahi karta.
- Sirf apne ya jise download karne ki permission ho aise content ke liye use karein.
- Instagram/YouTube ki website changes ki wajah se extraction kabhi fail ho sakta hai.
- Free hosts me time, memory, file-size, and bandwidth limits ho sakti hain.
- 1018p standard resolution nahi hai, isliye video option 1018p ko 1080p target samajhta hai.
