import requests

queries = [
    "ما هي متطلبات الحصول على مرتبة الشرف عند التخرج؟",
    "ما هو الحد الأدنى لقائمة الشرف؟",
    "ما هو الحد الأدنى للمعدل الذي يضع الطالب على قائمة الإنذار؟"
]

for q in queries:
    response = requests.post(
        "http://localhost:5000/api/query",
        json={"message": q, "session_id": None}
    )
    print(f"\nQ: {q}")
    print(f"Full response: {response.json()}")