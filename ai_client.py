import requests

API_URL = "http://localhost:8000/ask"

def ask_ai(question):
    try:
        response = requests.post(API_URL, json={"question": question}, timeout=3)
        if response.status_code == 200:
            return response.json().get("answer", "")
        else:
            return f"Ошибка: {response.status_code}"
    except Exception as e:
        return f"AI не отвечает: {e}"
