1. Open a terminal on the project root
2. python -m venv venv
3. venv\Scripts\activate
4. (If error occurs on step 2, run the ff and run step 2 again) Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
5. pip install -r requirements.txt
6. ./proto_compile.bat
7. use run.bat
8. open localhost:5000

TO BUILD:
1. Must be in virtual environment
2. pyinstaller training_server.spec
3. pyinstaller dashboard_client.spec
