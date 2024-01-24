from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from flask import Flask, request, render_template, session 
from flask import jsonify
from werkzeug.utils import secure_filename
import PyPDF2
import re
import os
import base64
import speech_recognition as sr
import openai
from gpt_index import SimpleDirectoryReader, GPTListIndex, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain.chat_models import ChatOpenAI
import sys
import speech_recognition as sr
import pyttsx3
import cv2

app = Flask(__name__)
app.secret_key = '\x96O\xae\x93\x829\x8f\xda\xfa>}ZV!\xba\x8f\xc4qV\xb2Xl\xda\x0f'
file_path = ""
#os.environ["OPENAI_API_KEY"] = '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'
#openai = "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" 
api_key = "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"
os.environ["OPENAI_API_KEY"] = api_key
ALLOWED_EXTENSIONS = {'pdf', 'txt'} 

conn = mysql.connector.connect(user='root', password='root', host='localhost', database='employee')
#conn = mysql.connector.connect(user='root', password='passwordSAMSAN!1234', host='localhost', database='employee')
cursor = conn.cursor()
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
engine = pyttsx3.init()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('globalchatbot.html')
def construct_index(directory_path):
    print("Inside construct_index. Directory path:", directory_path)
    max_input_size = 40960
    num_outputs = 5120
    max_chunk_overlap = 200
    chunk_size_limit = 6000
    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", max_tokens=num_outputs))
    documents = SimpleDirectoryReader(directory_path).load_data()
    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index.save_to_disk('index.json')
    print("index file createdSSS")
    return index
@app.route('/adminLogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        userDetails = request.form
        name = userDetails['name']
        emailId = userDetails['email']
        password = userDetails['password']
        print(f"Received form data - Name: {name}, Email: {emailId}, Password: {password}")
        correct_name = "Samsanlabs"
        correct_email = "samsanlabs123@gmail.com"
        correct_password = "samsan123"

        if name == correct_name and emailId == correct_email and password == correct_password:
            session['name'] = name
            session['emailId'] = emailId
            
            return render_template('user.html')
        else:
            error_message = "Invalid credentials. Please try again."
            print(f"Error: {error_message}")
            return render_template('admin.html', error_message=error_message)
    return render_template('admin.html')

@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        userDetails = request.form
        print(userDetails)
        name = userDetails['name']
        emailId = userDetails['email']
        password = userDetails['password']
        cursor.execute("SELECT * FROM chatboatuser1 WHERE name = %s AND emailId = %s", (name, emailId))
        existing_user = cursor.fetchone()

        if existing_user:
            print('User with the given name and email already exists in the database')
            return render_template('user.html', error_message="Already exit")
        cursor.execute("INSERT INTO chatboatuser1 (name, emailId, password) VALUES (%s, %s, %s)", (name, emailId, password))
        conn.commit()
        session['emailId'] = emailId
        return render_template('user.html', error_message="Create user successfully")
 
@app.route('/user_list',methods=['GET','POST'])
def user_list():
    cursor.execute("SELECT * FROM chatboatuser1")
    users = cursor.fetchall()
    return render_template('userlist.html', users=users)

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        userDetails = request.form
        #print(userDetails)
        name = userDetails['name']
        emailId = userDetails['email']
        password = userDetails['password']
        cursor.execute("SELECT * FROM chatboatuser1 WHERE name = %s AND emailId = %s AND password = %s", (name, emailId, password))

        existing_user = cursor.fetchone()

        if existing_user:
            session['name'] = name
            session['emailId'] = emailId
            return render_template('chatboat.html', name=name, emailId=emailId)
            #return render_template('globalchatbot.html', message1='Login successful')  
        if name != "correct_name" or emailId != "correct_email" or password != "correct_password":
            return render_template('globalchatbot.html', error_message="Invalid credentials. Please try again.")
        return "Name and Email not found. Please try again or sign up."
@app.route('/reset_password', methods=['POST'])
def reset_password():
    if request.method == 'POST':
        userDetails = request.form
        name = userDetails['name']
        emailId = userDetails['email']
        new_password = userDetails['new_password']
        cursor.execute("SELECT * FROM chatboatuser1 WHERE name = %s AND emailId = %s", (name, emailId))
        existing_user = cursor.fetchone()
        if existing_user:
            user_id = existing_user[0] 
            cursor.execute("UPDATE chatboatuser1 SET password = %s WHERE id = %s", (new_password, user_id))
            conn.commit()
            return render_template('globalchatbot.html', message="Password reset successfully.")
        else:
            return render_template('globalchatbot.html', error_message="User not found. Please provide correct name and email.")
        
@app.route('/chatbot')
def chatbot():
        return render_template('chatboat.html')
from flask import jsonify

@app.route('/local_chat', methods=['POST'])
def local_chat():
    user_role = request.json.get('user_role')
    if 'input_text' in request.json:
        input_text = request.json.get('input_text')
        context = request.json.get('context')
        index = GPTSimpleVectorIndex.load_from_disk('index.json')
        input_text_with_role_and_context = f"{input_text}. You act as {user_role}. Context: {context}"
        print("input text, role, and context", input_text_with_role_and_context)
        #response = index.query(input_text_with_role_and_context, response_mode="compact")
        response = {"response": "When refuelling at a self-service stand, it is important to take the necessary safety precautions, regardless of age, number of vehicles in the household, or household income. Make sure to turn off the engine and any other electrical equipment before refuelling. Do not smoke or use any open flames near the refuelling area. Wear protective clothing, such as gloves and safety glasses, to protect yourself from any potential spills. Make sure to keep any children away from the refuelling area. Additionally, be aware of any potential hazards, such as fuel spills, and take the necessary steps to clean them up. It is also important to consider the preferences of those who are likely to purchase a two-wheeler in the next 5 years, as indicated by the survey results. Factors such as style, environmental performance, safety, reliability, comfort, cargo-carrying capacity, and replacement part availability are all important considerations when refuelling at a self-service stand."}
    else:
        return jsonify({'error': 'Invalid request. Please provide either "input_text" or "speech_transcript".'})

    if response and response["response"] is not None:
        formatted_response = response["response"].replace('\n', '<br>')
        print("final response", formatted_response)
        return jsonify(formatted_response)
    #if response and response.response is not None:
        #formatted_response = response.response.replace('\n', '<br>')
        #print("final response", formatted_response)
        #return jsonify(formatted_response)
    else:
        return jsonify(response["response"])
    #else:
        #return jsonify(response.response)


    

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global file_path
    try:
        uploaded_file = request.files['file']

        if uploaded_file and allowed_file(uploaded_file.filename):
            filename = secure_filename(uploaded_file.filename)
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            static_folder_path = os.path.join(current_script_dir, "vectorIndex")
            os.makedirs(static_folder_path, exist_ok=True)
            file_path = os.path.join(static_folder_path, filename)
            
            uploaded_file.save(file_path)
            print("File saved at:", file_path)

            if filename.endswith('.pdf'):
                print("Processing PDF file...")
                with open(file_path, 'rb') as pdf_file:
                    pdf_data = base64.b64encode(pdf_file.read()).decode('utf-8')
                    folder_path = os.path.dirname(file_path)
                    index = construct_index(folder_path)
                    print("PDF file processed successfully.")
                    return render_template('chatboat.html')

            elif filename.endswith('.txt'):
                print("Processing TXT file...")
                with open(file_path, 'r') as file:
                    all_text = file.read()
                folder_path = os.path.dirname(file_path)
                index = construct_index(folder_path)
                print("TXT file processed successfully.")
                return render_template('chatboat.html')        
        else:
            return 'Invalid file type. Allowed types: .pdf, .txt'
    except Exception as e:
        return f"An error occurred: {str(e)}"

@app.route("/uploadlogo", methods=['GET', 'POST'])
def uploadlogo():
    global image_path
    global input_image_base64
    image_file = request.files["file"]
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    static_folder = os.path.join(current_script_dir, "static")
    os.makedirs(static_folder, exist_ok=True)
    image_path = os.path.join(static_folder, secure_filename(image_file.filename))
    image_file.save(image_path)
    input_image = cv2.imread(image_path)    
    if input_image is not None:
        _, input_image_png = cv2.imencode('.jpg', input_image)
        input_image_base64 = base64.b64encode(input_image_png).decode('utf-8')
        return render_template('chatboat.html', image_path=image_path, input_image_png=input_image_base64)
    else:
        return "Failed to load the image."

'''@app.route('/create_index', methods=['POST'])
def create_index():
    try:
        result = construct_index('C:/Users/hande/OneDrive/Desktop/chatboat/venv/vectorIndex/')
        return "Index created successfully"
    except Exception as e:
        # If rate limit error occurs, wait for 20 seconds and retry
        if "Rate limit reached" in str(e):
            time.sleep(20)
            return create_index()
        else:
            return f"An error occurred: {str(e)}"'''
@app.route('/logout',methods=['POST'])
def logout():
    return render_template('globalchatbot.html')
if __name__ == '__main__':
    app.run(debug=True)
