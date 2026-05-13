from music21 import converter, note, chord, tempo
import xml.etree.ElementTree as ET
import numpy as np
import os
import shutil
import subprocess
import tempfile


# ==========================================================
# 1. MusicXML → Notes 추출 (기존 로직 유지 + 안정화)
# ==========================================================
def extract_notes_from_musicxml(xml_path):
    """
    MusicXML 파일에서 악보 데이터 추출.
    단음 + 화음 모두 처리, 초(seconds) 단위로 변환.
    """
    try:
        score = converter.parse(xml_path)

        # BPM 감지
        bpm = 120
        for element in score.flatten():
            if isinstance(element, tempo.MetronomeMark):
                if element.number is not None:
                    bpm = float(element.number)
                    break

        if bpm == 120:
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                for sound in root.iter('sound'):
                    if sound.get('tempo'):
                        bpm = float(sound.get('tempo'))
                        break
            except Exception:
                pass

        print(f"-> BPM 감지: {bpm}")
        seconds_per_quarter = 60.0 / bpm
        expected_notes = []

        # ✅ part.flatten() 대신 score.flatten() 사용 시
        #    grand staff(피아노 양손)의 offset이 part별로 0부터 시작하는 문제 방지
        for part in score.parts:
            flat_part = part.flatten()
            for element in flat_part.notesAndRests:
                if isinstance(element, note.Note):
                    try:
                        start_sec = round(float(element.offset) * seconds_per_quarter, 3)
                        duration_sec = round(float(element.duration.quarterLength) * seconds_per_quarter, 3)
                        end_sec = round(start_sec + duration_sec, 3)
                        velocity = int(element.volume.velocity) if element.volume.velocity is not None else 64
                        expected_notes.append({
                            'note': element.nameWithOctave,
                            'pitch': element.pitch.midi,
                            'start': start_sec,
                            'end': end_sec,
                            'duration': duration_sec,
                            'velocity': velocity
                        })
                    except Exception:
                        continue

                elif isinstance(element, chord.Chord):
                    try:
                        start_sec = round(float(element.offset) * seconds_per_quarter, 3)
                        duration_sec = round(float(element.duration.quarterLength) * seconds_per_quarter, 3)
                        end_sec = round(start_sec + duration_sec, 3)
                        for n in element.notes:
                            velocity = int(n.volume.velocity) if n.volume.velocity is not None else 64
                            expected_notes.append({
                                'note': n.nameWithOctave,
                                'pitch': n.pitch.midi,
                                'start': start_sec,
                                'end': end_sec,
                                'duration': duration_sec,
                                'velocity': velocity
                            })
                    except Exception:
                        continue

        expected_notes.sort(key=lambda x: (x['start'], x['pitch']))
        return expected_notes

    except Exception as e:
        print(f"[모듈 1 오류] MusicXML 파일을 읽는 중 문제 발생: {e}")
        return []


# ==========================================================
# 2. 이미지 전처리 (OMR 정확도 향상의 핵심)
# ==========================================================
def preprocess_image_for_omr(image_path, output_path):
    """
    OMR 정확도 향상을 위한 이미지 전처리:
    - 그레이스케일 변환
    - 대비 향상
    - 노이즈 제거 (median filter)
    - 해상도 정규화 (300 DPI 권장)
    """
    try:
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps

        img = Image.open(image_path)

        # EXIF 회전 보정 (휴대폰 촬영 사진 대비)
        img = ImageOps.exif_transpose(img)

        # 그레이스케일
        if img.mode != 'L':
            img = img.convert('L')

        # 대비 향상 (악보의 흑백 대비 강조)
        img = ImageEnhance.Contrast(img).enhance(1.6)

        # 노이즈 제거
        img = img.filter(ImageFilter.MedianFilter(size=3))

        # 해상도가 너무 작으면 업스케일 (OMR은 200~300 DPI 필요)
        min_width = 1500
        if img.width < min_width:
            ratio = min_width / img.width
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # oemer는 RGB 입력 기대
        img = img.convert('RGB')
        img.save(output_path, 'PNG', dpi=(300, 300))
        return output_path

    except Exception as e:
        print(f"[전처리 경고] 이미지 전처리 실패, 원본 사용: {e}")
        # 실패 시 원본 복사
        shutil.copy(image_path, output_path)
        return output_path


# ==========================================================
# 3. PDF → Image 변환
# ==========================================================
def pdf_to_images(pdf_path, output_dir, dpi=300):
    """
    PDF를 페이지별 이미지로 변환.
    poppler 설치 필요 (Windows: poppler 바이너리, macOS: brew install poppler).
    """
    try:
        from pdf2image import convert_from_path

        os.makedirs(output_dir, exist_ok=True)
        images = convert_from_path(pdf_path, dpi=dpi)
        image_paths = []
        for i, img in enumerate(images):
            img_path = os.path.join(output_dir, f"page_{i:03d}.png")
            img.save(img_path, "PNG")
            image_paths.append(img_path)
        print(f"-> PDF에서 {len(image_paths)}페이지 추출 완료")
        return image_paths
    except ImportError:
        print("[모듈 1 오류] pdf2image가 설치되어 있지 않습니다. 'pip install pdf2image' 후 poppler도 설치하세요.")
        return []
    except Exception as e:
        print(f"[모듈 1 오류] PDF 변환 중 문제 발생: {e}")
        return []


# ==========================================================
# 4. Image → MusicXML (OMR, oemer 사용)
# ==========================================================
def image_to_musicxml(image_path):
    """
    이미지(JPEG/PNG)를 OMR로 분석하여 MusicXML로 변환.
    oemer 라이브러리 사용 (pip install oemer).

    Returns:
        생성된 MusicXML 파일 경로 (실패 시 None)
    """
    # 각 호출마다 고유 작업 디렉토리 (이전 결과 잔존 방지)
    work_dir = tempfile.mkdtemp(prefix="omr_")

    try:
        # 1) 전처리
        preprocessed = os.path.join(work_dir, "preprocessed.png")
        preprocess_image_for_omr(image_path, preprocessed)

        # 2) oemer 실행
        print(f"-> OMR 실행 중... (이미지: {os.path.basename(image_path)})")
        try:
            result = subprocess.run(
                ["oemer", preprocessed, "-o", work_dir],
                capture_output=True, text=True, timeout=600
            )
        except FileNotFoundError:
            print("[모듈 1 오류] oemer 명령어를 찾을 수 없습니다.")
            print("              설치: pip install oemer")
            return None
        except subprocess.TimeoutExpired:
            print("[모듈 1 오류] OMR 처리 시간 초과 (10분)")
            return None

        if result.returncode != 0:
            print(f"[모듈 1 오류] OMR 처리 실패:")
            print(f"  stderr: {result.stderr[:500]}")
            return None

        # 3) 결과 XML 찾기
        xml_files = [
            os.path.join(work_dir, f)
            for f in os.listdir(work_dir)
            if f.endswith(".musicxml") or f.endswith(".xml")
        ]

        if not xml_files:
            print("[모듈 1 오류] OMR 결과 XML 파일을 찾을 수 없음")
            return None

        # 영구 위치로 복사 (work_dir은 곧 삭제됨)
        permanent_path = image_path + ".omr.musicxml"
        shutil.copy(xml_files[0], permanent_path)
        print(f"-> OMR 완료: {permanent_path}")
        return permanent_path

    except Exception as e:
        print(f"[모듈 1 오류] OMR 변환 중 문제 발생: {e}")
        return None
    finally:
        # 작업 디렉토리 정리
        shutil.rmtree(work_dir, ignore_errors=True)


# ==========================================================
# 5. 파일 형식 자동 분기
# ==========================================================
def extract_notes_from_sheet(sheet_path):
    """
    악보 파일 형식에 따라 자동 처리.
    지원 형식: .xml, .musicxml, .mid, .midi, .jpg, .jpeg, .png, .pdf
    """
    if not os.path.exists(sheet_path):
        print(f"[모듈 1 오류] 파일을 찾을 수 없음: {sheet_path}")
        return []

    ext = os.path.splitext(sheet_path)[1].lower()

    # --- MusicXML 직접 처리 ---
    if ext in ['.xml', '.musicxml']:
        print(f"-> MusicXML 파일 감지")
        return extract_notes_from_musicxml(sheet_path)

    # --- MIDI 처리 ---
    elif ext in ['.mid', '.midi']:
        print(f"-> MIDI 파일 감지")
        try:
            score = converter.parse(sheet_path)
            tmp_xml = os.path.join(tempfile.gettempdir(), "tmp_midi_converted.musicxml")
            score.write('musicxml', fp=tmp_xml)
            notes = extract_notes_from_musicxml(tmp_xml)
            if os.path.exists(tmp_xml):
                os.remove(tmp_xml)
            return notes
        except Exception as e:
            print(f"[모듈 1 오류] MIDI 변환 실패: {e}")
            return []

    # --- 이미지 처리 (JPEG/PNG) ---
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        print(f"-> 이미지 파일 감지 → OMR 분석 시작")
        xml_path = image_to_musicxml(sheet_path)
        if xml_path:
            notes = extract_notes_from_musicxml(xml_path)
            # OMR 결과 XML 정리 (디버깅 시 주석 처리 권장)
            if os.path.exists(xml_path):
                os.remove(xml_path)
            return notes
        return []

    # --- PDF 처리 ---
    elif ext == '.pdf':
        print(f"-> PDF 파일 감지 → 이미지 변환 후 OMR 분석 시작")
        work_dir = tempfile.mkdtemp(prefix="pdf_omr_")
        try:
            image_paths = pdf_to_images(pdf_path=sheet_path, output_dir=work_dir, dpi=300)
            if not image_paths:
                return []

            all_notes = []
            page_offset = 0.0  # 페이지 간 시간 오프셋
            PAGE_GAP_SEC = 0.5  # 페이지 사이 여백 (선택)

            for i, img_path in enumerate(image_paths):
                print(f"  - 페이지 {i + 1}/{len(image_paths)} 처리 중")
                xml_path = image_to_musicxml(img_path)
                if not xml_path:
                    print(f"  - 페이지 {i + 1} OMR 실패, 건너뜀")
                    continue

                page_notes = extract_notes_from_musicxml(xml_path)
                if os.path.exists(xml_path):
                    os.remove(xml_path)

                if not page_notes:
                    continue

                # 시간 오프셋 적용
                for n in page_notes:
                    n['start'] = round(n['start'] + page_offset, 3)
                    n['end'] = round(n['end'] + page_offset, 3)

                all_notes.extend(page_notes)

                # 다음 페이지 오프셋 갱신
                page_offset = page_notes[-1]['end'] + PAGE_GAP_SEC

            all_notes.sort(key=lambda x: (x['start'], x['pitch']))
            return all_notes
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    else:
        print(f"[모듈 1 오류] 지원하지 않는 파일 형식: {ext}")
        print(f"              지원 형식: .xml, .musicxml, .mid, .midi, .jpg, .jpeg, .png, .pdf")
        return []


# ==========================================================
# 6. DTW용 onset 시퀀스 추출
# ==========================================================
def extract_onset_sequence(sheet_path):
    """DTW 정렬을 위한 onset/pitch 시퀀스 추출."""
    try:
        notes = extract_notes_from_sheet(sheet_path)
        if not notes:
            return np.array([]), np.array([])
        return (
            np.array([n['start'] for n in notes]),
            np.array([n['pitch'] for n in notes])
        )
    except Exception as e:
        print(f"[모듈 1 오류] onset 추출 중 문제 발생: {e}")
        return np.array([]), np.array([])
    
def get_sheet_bpm(sheet_path):
    """
    악보 파일에서 BPM(템포) 추출.
    
    Returns:
        float: BPM 값 (성공 시)
        None: BPM 감지 실패 시 (PDF/이미지, 또는 템포 정보 없는 파일)
    """
    if not os.path.exists(sheet_path):
        return None
    
    ext = os.path.splitext(sheet_path)[1].lower()
    
    # XML/MusicXML: 직접 파싱
    if ext in ['.xml', '.musicxml']:
        return _read_bpm_from_xml(sheet_path)
    
    # MIDI: music21로 파싱
    elif ext in ['.mid', '.midi']:
        try:
            score = converter.parse(sheet_path)
            for element in score.flatten():
                if isinstance(element, tempo.MetronomeMark) and element.number:
                    return float(element.number)
        except Exception as e:
            print(f"[BPM 감지 경고] MIDI 파싱 실패: {e}")
        return None
    
    # 이미지/PDF: OMR 결과에서 BPM 가져오기 (옵션)
    # 비용이 크니까 기본은 None 반환하고 quantize 비활성으로 동작
    elif ext in ['.jpg', '.jpeg', '.png', '.pdf']:
        print(f"-> [BPM 자동 감지] 이미지/PDF는 OMR 후에야 BPM 추출 가능")
        print(f"-> 일단 None 반환 (quantize 비활성 모드로 동작)")
        return None
    
    return None


def _read_bpm_from_xml(xml_path):
    """MusicXML 내부에서 BPM 추출. music21 우선, 실패 시 직접 XML 파싱."""
    # 시도 1: music21의 MetronomeMark
    try:
        score = converter.parse(xml_path)
        for element in score.flatten():
            if isinstance(element, tempo.MetronomeMark) and element.number is not None:
                return float(element.number)
    except Exception:
        pass
    
    # 시도 2: <sound tempo="X"/> 직접 파싱
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for sound in root.iter('sound'):
            if sound.get('tempo'):
                return float(sound.get('tempo'))
    except Exception:
        pass
    
    return None