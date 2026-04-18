import requests

#Sample questions used to test the query endpoint
queries = [
    "ما هي متطلبات الحصول على مرتبة الشرف عند التخرج؟",
    "ما هو الحد الأدنى لقائمة الشرف؟",
    "ما هو الحد الأدنى للمعدل الذي يضع الطالب على قائمة الإنذار؟"
]

#Send each question to the backend and print the returned JSON
for q in queries:
    response = requests.post(
        "http://localhost:5000/api/query",
        json={"message": q, "session_id": None}
    )
    print(f"\nQ: {q}")
    print(f"Full response: {response.json()}")