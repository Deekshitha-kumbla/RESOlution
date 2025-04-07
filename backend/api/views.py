from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse

@api_view(['GET'])
#def hello_world(request):
    #eturn Response({"message": "Hello from Django!"}, content_type="application/json")
#def get_benchmark(request):
   # return Response({"benchmark": "Performance Score", "value": 95})
def get_benchmark(request):
    data = {
        "message": "Benchmark Results",
        "results": [  
            {"id": 1, "name": "Test 1", "score": 95},
            {"id": 2, "name": "Test 2", "score": 88}
        ]
    }
    return JsonResponse(data)
