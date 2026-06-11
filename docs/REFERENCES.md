# 참고문헌 (References)

> 본 프로젝트 개발에 직접 사용되거나 참고한 논문, 기술 문서, 라이브러리 목록입니다.

---

## 1. 핵심 모델 및 알고리즘

### 1-1. 피아노 음표 추출 (module2)

**[1]** Kong, Q., Li, B., Song, X., Wan, Y., & Wang, Y. (2021).  
*High-resolution Piano Transcription with Pedals by Regressing Onset and Offset Times.*  
IEEE/ACM Transactions on Audio, Speech, and Language Processing, 29, 3707–3717.  
https://doi.org/10.1109/TASLP.2021.3136251  
→ `piano-transcription-inference` 라이브러리의 기반 논문. 본 프로젝트의 module2.py에서 WAV → 음표 추출에 사용.

**[2]** Kong, Q., Cao, Y., Iqbal, T., Wang, Y., Wang, W., & Plumbley, M. D. (2020).  
*PANNs: Large-Scale Pretrained Audio Neural Networks for Audio Pattern Recognition.*  
IEEE/ACM Transactions on Audio, Speech, and Language Processing, 28, 2880–2894.  
https://doi.org/10.1109/TASLP.2020.3030497  
→ piano_transcription_inference 모델 구조의 기반 아키텍처.

---

### 1-2. 악보 파싱 (module1)

**[3]** Cuthbert, M. S., & Ariza, C. (2010).  
*music21: A Toolkit for Computer-Aided Musicology and Symbolic Music Data.*  
Proceedings of the 11th International Society for Music Information Retrieval Conference (ISMIR 2010), 637–642.  
https://music21.mit.edu  
→ module1.py에서 MusicXML 파싱 및 음표 추출에 사용.

**[4]** Bellini, P., & Nesi, P. (2001).  
*WEDELMUSIC Format: An XML Music Notation Format for Emerging Applications.*  
Proceedings of the First International Conference on Web Delivering of Music (WEDELMUSIC 2001), 79–86.  
https://doi.org/10.1109/WDM.2001.990172  
→ MusicXML 포맷의 기초가 된 XML 음악 표기 연구.

---

### 1-3. 오디오 신호 처리 (module2, chord_upgrade)

**[5]** McFee, B., Raffel, C., Liang, D., Ellis, D. P., McVicar, M., Battenberg, E., & Nieto, O. (2015).  
*librosa: Audio and Music Signal Analysis in Python.*  
Proceedings of the 14th Python in Science Conference (SciPy 2015), 18–25.  
https://doi.org/10.25080/Majora-7b98e3ed-003  
→ module2.py 오디오 리샘플링, chord_upgrade.py CQT 계산에 사용.

**[6]** Brown, J. C. (1991).  
*Calculation of a Constant Q Spectral Transform.*  
The Journal of the Acoustical Society of America, 89(1), 425–434.  
https://doi.org/10.1121/1.400476  
→ chord_upgrade.py에서 화음 재검증에 사용하는 Constant-Q Transform(CQT)의 원천 논문.

**[7]** Müller, M. (2015).  
*Fundamentals of Music Processing: Audio, Analysis, Algorithms, Applications.*  
Springer.  
ISBN: 978-3-319-21944-8  
→ 음표 비교·타이밍 오차 계산(module3) 설계 시 참고.

---

### 1-4. MIDI 처리

**[8]** Raffel, C., & Ellis, D. P. W. (2014).  
*Intuitive Analysis, Creation and Manipulation of MIDI Data with pretty_midi.*  
Proceedings of the 15th International Society for Music Information Retrieval Conference (ISMIR 2014), Late Breaking/Demo Session.  
http://colinraffel.com/publications/ismir2014intuitive.pdf  
→ module2.py에서 piano_transcription 모델의 MIDI 출력 처리에 사용.

---

### 1-5. 광학 악보 인식 (OMR)

**[9]** Bitteur, H. (2012).  
*Audiveris: An Open Music Score Digitization Project.*  
https://github.com/Audiveris/audiveris  
→ module1.py에서 PDF/이미지 악보를 MusicXML로 변환하는 데 사용.

**[10]** Pacha, A., Hajič, J., & Calvo-Zaragoza, J. (2018).  
*A Baseline for General Music Object Detection with Deep Learning.*  
Applied Sciences, 8(9), 1488.  
https://doi.org/10.3390/app8091488  
→ OMR(Optical Music Recognition) 기술의 딥러닝 기반 접근법 참고.

---

## 2. AI 피드백 생성 (module4, backend)

**[11]** OpenAI. (2024).  
*GPT-4o System Card.*  
https://openai.com/research/gpt-4o-system-card  
→ module4.py 및 Go 백엔드(gpt.go, gpt_stream.go)에서 GPT-4o-mini 피드백 생성에 사용.

**[12]** Qwen Team, Alibaba Cloud. (2024).  
*Qwen2.5 Technical Report.*  
arXiv:2412.15115.  
https://arxiv.org/abs/2412.15115  
→ module4.py의 Ollama 로컬 LLM 옵션으로 사용되는 Qwen 2.5-1.5B 모델.

**[13]** Ollama. (2024).  
*Ollama: Run Large Language Models Locally.*  
https://github.com/ollama/ollama  
→ 로컬 환경에서 Qwen 2.5-1.5B 실행 인프라로 사용.

---

## 3. 딥러닝 프레임워크

**[14]** Paszke, A., Gross, S., Massa, F., Lerer, A., Bradbury, J., Chanan, G., ... & Chintala, S. (2019).  
*PyTorch: An Imperative Style, High-Performance Deep Learning Library.*  
Advances in Neural Information Processing Systems (NeurIPS 2019), 32, 8024–8035.  
https://arxiv.org/abs/1912.01703  
→ piano_transcription_inference 모델 실행 백엔드.

**[15]** Abadi, M., Agarwal, A., Barham, P., Brevdo, E., Chen, Z., Citro, C., ... & Zheng, X. (2016).  
*TensorFlow: Large-Scale Machine Learning on Heterogeneous Distributed Systems.*  
arXiv:1603.04467.  
https://arxiv.org/abs/1603.04467  
→ piano_transcription_inference의 TensorFlow 의존성 (macOS: tensorflow-macos 2.16.2).

---

## 4. 백엔드 서버

**[16]** Go Team, Google. (2009–).  
*The Go Programming Language.*  
https://go.dev  
→ 백엔드 HTTP 서버(backend/) 구현에 사용. Go 1.24.

**[17]** joho. (2023).  
*godotenv: A Go port of Ruby's dotenv library.*  
https://github.com/joho/godotenv  
→ Go 서버에서 `.env` 파일 로딩에 사용.

**[18]** W3C. (2015).  
*Server-Sent Events (SSE) — W3C Recommendation.*  
https://www.w3.org/TR/eventsource/  
→ GPT 피드백 스트리밍(GET /api/feedback/stream) 구현의 기반 표준.

---

## 5. 프론트엔드 (PWA)

**[19]** Meta Platforms. (2013–).  
*React: A JavaScript Library for Building User Interfaces.*  
https://react.dev  
→ 프론트엔드 UI 구현에 사용. React 19.

**[20]** Vite Team. (2020–).  
*Vite: Next Generation Frontend Tooling.*  
https://vitejs.dev  
→ React 번들러 및 개발 서버. Vite 8.

**[21]** antfu, et al. (2022–).  
*vite-plugin-pwa: Zero-config PWA Plugin for Vite.*  
https://github.com/vite-pwa/vite-plugin-pwa  
→ PWA manifest, Service Worker 자동 생성에 사용.

**[22]** W3C / WHATWG. (2023).  
*Web Application Manifest.*  
https://www.w3.org/TR/appmanifest/  
→ PWA "홈 화면에 추가" 기능의 기반 표준.

---

## 6. 음악 교육 및 자동 평가 관련 선행 연구

**[23]** Raphael, C. (2001).  
*Automatic Segmentation of Acoustic Musical Signals Using Hidden Markov Models.*  
IEEE Transactions on Pattern Analysis and Machine Intelligence, 21(4), 360–370.  
https://doi.org/10.1109/34.761266  
→ 연주 자동 평가 분야의 기반 연구 참고.

**[24]** Nakamura, E., Yoshii, K., & Sagayama, S. (2015).  
*Performance Error Detection and Post-Processing for Fast and Accurate Symbolic Music Alignment.*  
Proceedings of the 16th International Society for Music Information Retrieval Conference (ISMIR 2015), 347–353.  
→ 악보-연주 음표 정렬(module3 compare_notes) 설계 시 참고.

**[25]** Dixon, S. (2005).  
*MATCH: A Music Alignment Tool Chest.*  
Proceedings of the 6th International Society for Music Information Retrieval Conference (ISMIR 2005), 492–497.  
→ 음악 정렬 알고리즘 설계 참고.

---

## 7. 개발 도구 및 기타

**[26]** Pytest Development Team. (2004–).  
*pytest: Full-featured Python Testing Tool.*  
https://pytest.org  
→ code/tests/ 단위 테스트 22개 실행 프레임워크.

**[27]** Anaconda, Inc. (2012–).  
*Anaconda Distribution.*  
https://www.anaconda.com  
→ Python 분석 파이프라인 환경 관리(capstone_music conda 환경).

**[28]** FFmpeg Team. (2000–).  
*FFmpeg: A Complete, Cross-Platform Solution to Record, Convert and Stream Audio and Video.*  
https://ffmpeg.org  
→ WAV 외 오디오 포맷 변환 시 사용 권장 도구(트러블슈팅 안내).

---

> 작성일: 2026-06-11  
> 브랜치: `leejy_mac` | 저장소: https://github.com/LEEjy0431/capstone_music_ver2
