from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from church_core.permissions import IsChurchMember

# import requests # requests 라이브러리 설치 필요 (pip install requests)

class BibleVerseView(APIView):
    permission_classes = [IsAuthenticated, IsChurchMember]

    def get(self, request, church_id, book, chapter, verse, format=None):
        # TODO: 외부 성경 API 연동 로직 구현
        # 예시: https://bible-api.com/john%203:16
        # response = requests.get(f"https://bible-api.com/{book}%20{chapter}:{verse}")
        # if response.status_code == 200:
        #     data = response.json()
        #     return Response({
        #         "verse": data.get('text'),
        #         "reference": data.get('reference')
        #     }, status=status.HTTP_200_OK)
        # else:
        #     return Response({"detail": "성경 구절을 가져오는데 실패했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Placeholder response
        return Response({
            "verse": f"이는 하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니 이는 저를 믿는 자마다 멸망치 않고 영생을 얻게 하려 하심이니라. (요한복음 3장 16절)",
            "reference": f"{book} {chapter}:{verse}"
        }, status=status.HTTP_200_OK)