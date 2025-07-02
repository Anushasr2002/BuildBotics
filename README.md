Very IMP: You have create a Gemini API key in this website:https://aistudio.google.com/app/apikey from your mobile and paste it in the .env file create under the config folder 

*********
Very IMP: Do this before and after committing to github
1. In inventory_agent.py change the file path for inventory path
2. In scheduling_agent.py change the file path for demand_path, inventory_path, inventory_status_path
3. Add/Remove the api key from .env file
4. Also delete the virtual environment and node modules folder created before committing to github
*********

Instructions for backend setup.
1.Open this folder in VS code.
2.In the terminal, use this command to "cd backend" to change the directory to backend.
3.Create a new virtual environment using the following code "python -m venv {give your own venv name without these curly braces}".
4.Activate the venv using "{Your venv name}\Scripts\activate".
5.Once activated, use the "req1.txt" file to install the requirements using "pip install -r req1.txt".
6.Wait for sometime till it finishes installation, after that using this following code to start the application "uvicorn api.app:app --host 0.0.0.0 --port 8000
7.You will see the application running.

Note:Steps 1 to 3 are need to be done only once. BUt know how to change the directory to run the application.

Instructions for Frontend setup.
1.Create a new terminal using the "..." found near the "run" option.
2.Change the directory to frontend usong the "cd frontend"
3.Now write "npm install" and give enter.
4.Wait till the installation completes. And put "npm start" and you will see the webapp running.

Note: Steps 1 to 3 are need to be done only once.

IMP: When testing or running it, just activate backend by following from the step 4 for backend and from step 4 for frontend.

