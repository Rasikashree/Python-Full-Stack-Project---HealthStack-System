from rest_framework import serializers

class SymptomInputSerializer(serializers.Serializer):
    symptoms = serializers.ListField(child=serializers.CharField(max_length=128), allow_empty=False)

class DoctorRecommendationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    department_name = serializers.CharField(required=False, allow_blank=True)
    score = serializers.FloatField(required=False)

const SYMPTOM_CATEGORIES = [
  { id: 'general', name: 'General', symptoms: [
    { code: 'fever', name: 'Fever' },
    { code: 'fatigue', name: 'Fatigue' },
    { code: 'headache', name: 'Headache' },
    { code: 'nausea', name: 'Nausea' }
  ]},
  { id: 'resp', name: 'Respiratory', symptoms: [
    { code: 'cough', name: 'Cough' },
    { code: 'shortness of breath', name: 'Shortness of Breath' },
    { code: 'chest pain', name: 'Chest Pain' }
  ]},
  { id: 'neuro', name: 'Neurological', symptoms: [
    { code: 'dizziness', name: 'Dizziness' },
    { code: 'memory issues', name: 'Memory Issues' }
  ]},
  { id: 'derm', name: 'Dermatology', symptoms: [
    { code: 'rash', name: 'Rash' },
    { code: 'itching', name: 'Itching' }
  ]}
];