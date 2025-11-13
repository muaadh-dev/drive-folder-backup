import os
import os.path
import json
from tkinter import Tk, Label, Button, filedialog, messagebox
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES=["https://www.googleapis.com/auth/drive"]
FOLDER_JSON = "last_folder.json"
selected_folder_path = ""

def load_last_folder():
    if os.path.exists(FOLDER_JSON):
        with open(FOLDER_JSON, "r") as f:
            data = json.load(f)
            return data.get("folder_path", "")
    return ""

def save_folder(path):
    with open(FOLDER_JSON, "w") as f:
        json.dump({"folder_path": path}, f)

def choose_folder():
    global selected_folder_path
    path = filedialog.askdirectory(title="اختر مجلدًا جديدًا")
    if path and os.path.exists(path):
        folder_var.config(text=path)
        save_folder(path)
        selected_folder_path = path

def start_upload():
    global selected_folder_path
    folder_path = selected_folder_path or load_last_folder()
    if not folder_path or not os.path.exists(folder_path):
        messagebox.showwarning("Error","❌ لم يتم اختيار أي مجلد.")
        return
    #This is for authorization and authentication
    creds=None
    if os.path.exists("token.json"):
        creds=Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        #Access drive API with our Autherization
        service=build("drive", "v3", credentials=creds)
        folder_name = "Backup_" + datetime.now().strftime("%Y_%m_%d")
        response = service.files().list(q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'", spaces='drive').execute()
        if not response['files']:
            file_metadata ={
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder"}
            file = service.files().create(body=file_metadata, fields="id").execute()
            folder_id = file.get('id')
        else:
            folder_id=response['files'][0]['id']
        if not folder_path or not os.path.exists(folder_path):
            messagebox.showerror("Error","❌ لم يتم اختيار أي مجلد.")
            exit()

        for file in os.listdir(folder_path):
            full_path = os.path.join(folder_path, file)
            if not os.path.isfile(full_path):
                messagebox.showinfo("Error",f"{full_path} \nمجلد ولا يمكن رفعه")
                continue  # تجاهل المجلدات الفرعية

            file_metadata ={
                "name": file,
                "parents": [folder_id]}
            media = MediaFileUpload(full_path)
            upload_file = service.files().create(body=file_metadata,media_body=media,fields="id").execute()
            messagebox.showinfo("Backed up","file: " + file) 
        messagebox.showinfo("Backed up", f"✅ Backup file from:\n{folder_path}")
    except HttpError as e:
        messagebox.showerror("Error: " + str(e))

# واجهة بسيطة
root = Tk()
root.title("اختيار مجلد للرفع")
root.geometry("500x150")

last_path = load_last_folder()
folder_var = Label(root, text=last_path if last_path else "لم يتم اختيار مجلد بعد", anchor="w", width=60)
folder_var.pack(pady=10)

Button(root, text="📂 اختر مجلد جديد", command=choose_folder).pack(pady=5)
Button(root, text="⬆️ ابدأ الرفع", command=start_upload).pack(pady=5)

root.mainloop()