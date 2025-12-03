1. Open a terminal on the project root
2. python -m venv venv
3. venv\Scripts\activate
5. (If error occurs on step 2, run the ff and run step 2 again) Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
6. pip install --upgrade pip
7. pip install -r requirements.txt
8. ./proto_compile.bat
9. use run.bat
10. open localhost:5000

TO BUILD:
1. Must be in virtual environment
2. pip install pyinstaller
3. pyinstaller training_server.spec
4. pyinstaller dashboard_client.spec
