# 잠뜰 TV 팬 웹 (Streamlit)

기존 `index.html`의 콘텐츠 구조와 하늘색 테마를 바탕으로 Streamlit 앱으로 재구성했습니다.

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud 배포

1. 이 폴더의 파일을 GitHub 저장소 루트에 업로드합니다.
2. Streamlit Community Cloud에서 해당 저장소를 선택합니다.
3. Main file path를 `app.py`로 지정하고 Deploy 합니다.
4. 앱의 Settings > Secrets에 아래 설정을 추가합니다.

```toml
ADMIN_PASSWORD = "관리자용-새-비밀번호"
GUEST_PASSWORD = "게스트용-새-비밀번호"
FIREBASE_URL = "https://프로젝트-default-rtdb.asia-southeast1.firebasedatabase.app"
```

`FIREBASE_URL`은 원본 HTML에서 사용하던 Firebase Realtime Database URL을 확인해 입력하세요.
비밀번호는 원본 HTML에 노출되어 있던 값을 재사용하지 말고 새 비밀번호로 변경하세요.

## 데이터 관련 주의

- 시리즈, 단편 영상, 후기는 기존 데이터 구조(`/jt/series`, `/jt/singles`, `/jt/reviews`)와 호환되도록 저장합니다.
- Firebase URL이 비어 있으면 데이터는 서버에 영구 저장되지 않고 현재 Streamlit 세션에만 유지됩니다.
- 원본 HTML은 Firebase REST API를 인증 없이 호출했습니다. Firebase Realtime Database Rules가 공개 읽기/쓰기를 허용한다면 누구나 데이터를 읽거나 바꿀 수 있습니다. 실제 배포 전 Firebase Rules와 인증을 별도로 점검하세요.
- Streamlit 로그인은 UI 접근을 나누는 간단한 앱 비밀번호 방식입니다. 민감한 개인정보나 고위험 데이터를 저장하는 용도로 사용하지 마세요.
- 시청 체크와 에피소드 메모는 개인 세션 상태로 관리하며, 공유 Firebase에는 업로드하지 않습니다.
