from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ai_matcher.serializers import SymptomInputSerializer, DoctorRecommendationSerializer
from ai_matcher.services.inference import predict_symptoms
from ai_matcher.services.recommenders import recommend_doctors

class SymptomCheckerView(APIView):
    def post(self, request):
        ser = SymptomInputSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"error": ser.errors}, status=status.HTTP_400_BAD_REQUEST)
        data = predict_symptoms(ser.validated_data["symptoms"])
        return Response(data, status=200)

class DoctorMatchingView(APIView):
    def post(self, request):
        ser = SymptomInputSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"error": ser.errors}, status=status.HTTP_400_BAD_REQUEST)
        doctors = recommend_doctors(ser.validated_data["symptoms"])
        out = DoctorRecommendationSerializer(doctors, many=True)
        return Response(out.data, status=200)