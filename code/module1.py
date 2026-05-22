from music21 import converter, note, chord, tempo
import xml.etree.ElementTree as ET
import numpy as np
import base64
import json
import os
import re
import shutil
import tempfile
import zipfile


# ─────────────────────────────────────────────
# Claude Vision 프롬프트
# ─────────────────────────────────────────────

def _pitch_to_midi(pitch_name):
    """'C4', 'F#3', 'Bb5', 'G#2' 같은 음이름을 MIDI 번호로 변환."""
    _NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    m = re.match(r'([A-Ga-g])([#b]?)(-?\d+)', pitch_name.strip())
    if not m:
        return 60  # fallback: C4
    n, acc, oct_ = m.group(1).upper(), m.group(2), int(m.group(3))
    midi = (oct_ + 1) * 12 + _NOTE[n]
    if acc == '#':
        midi += 1
    elif acc == 'b':
        midi -= 1
    return midi


# ─────────────────────────────────────────────
# 2. Claude Vision → Notes
# ─────────────────────────────────────────────

def _image_to_notes_via_claude(image_path, fallback_bpm=120):
    """
    Claude Vision API로 악보 이미지를 분석해 음표 리스트를 반환.

    Returns:
        (notes: list[dict], bpm: float)
    """
    try:
        import anthropic
    except ImportError:
        print("[Claude Vision 오류] anthropic 패키지 없음")
        print("                    설치: pip install anthropic")
        return [], fallback_bpm

    # 이미지 → base64
    ext = os.path.splitext(image_path)[1].lower()
    media_type = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.bmp': 'image/png',
        '.tiff': 'image/png', '.tif': 'image/png',
    }.get(ext, 'image/jpeg')

    with open(image_path, 'rb') as f:
        img_b64 = base64.standard_b64encode(f.read()).decode('utf-8')

    print(f"-> Claude Vision 분석 중: {os.path.basename(image_path)}")

    # API 호출
    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=4096,
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'source': {
                            'type': 'base64',
                            'media_type': media_type,
                            'data': img_b64,
                        }
                    },
                    {'type': 'text', 'text': _SHEET_PROMPT}
                ]
            }]
        )
    except Exception as e:
        print(f"[Claude Vision 오류] API 호출 실패: {e}")
        return [], fallback_bpm

    # JSON 파싱
    raw = response.content[0].text.strip()
    data = _parse_json_response(raw)
    if data is None:
        print("[Claude Vision 오류] 응답 JSON 파싱 실패")
        print(f"  응답 앞부분: {raw[:300]}")
        return [], fallback_bpm

    # BPM 결정
    bpm = float(data.get('bpm') or fallback_bpm)
    spq = 60.0 / bpm  # seconds per quarter note

    # notes 변환
    notes_out = []
    for n in data.get('notes', []):
        try:
            offset_q = float(n['offset_quarters'])
            dur_q    = float(n['duration_quarters'])
            start    = round(offset_q * spq, 3)
            dur      = round(dur_q * spq, 3)
            end      = round(start + dur, 3)
            midi     = int(n.get('midi') or _pitch_to_midi(n['pitch']))

            if dur < 0.02:  # 너무 짧은 음표 제거
                continue

            notes_out.append({
                'note':     n['pitch'],
                'pitch':    midi,
                'start':    start,
                'end':      end,
                'duration': dur,
                'velocity': 64,
            })
        except Exception:
            continue

    notes_out.sort(key=lambda x: (x['start'], x['pitch']))
    print(f"-> Claude Vision 완료: {len(notes_out)}개 음표 (BPM={bpm})")
    return notes_out, bpm


def _parse_json_response(raw):
    """응답 텍스트에서 JSON을 안전하게 추출."""
    # 1) 순수 JSON
    try:
        return json.loads(raw)
    except Exception:
        pass

    # 2) ```json ... ``` 또는 ``` ... ``` 블록
    blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)```', raw)
    for block in blocks:
        try:
            return json.loads(block.strip())
        except Exception:
            continue

    # 3) { ... } 에서 첫 번째 JSON 객체 추출
    m = re.search(r'\{[\s\S]*\}', raw)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass

    return None


# ─────────────────────────────────────────────
# 3. MusicXML → Notes
# ─────────────────────────────────────────────

def extract_notes_from_musicxml(xml_path):
    """MusicXML / MXL 파일에서 음표 데이터 추출. 초(seconds) 단위."""
    try:
        score = converter.parse(xml_path)

        bpm = 120.0
        for element in score.flatten():
            if isinstance(element, tempo.MetronomeMark) and element.number is not None:
                bpm = float(element.number)
                break

        if bpm == 120.0 and xml_path.endswith(('.xml', '.musicxml')):
            try:
                tree = ET.parse(xml_path)
                for sound in tree.getroot().iter('sound'):
                    if sound.get('tempo'):
                        bpm = float(sound.get('tempo'))
                        break
            except Exception:
                pass

        print(f"-> BPM 감지: {bpm}")
        spq = 60.0 / bpm
        notes_out = []

        for part in score.parts:
            for element in part.flatten().notesAndRests:

                if isinstance(element, note.Note):
                    try:
                        start = round(float(element.offset) * spq, 3)
                        dur   = round(float(element.duration.quarterLength) * spq, 3)
                        end   = round(start + dur, 3)
                        vel   = int(element.volume.velocity) if element.volume.velocity else 64
                        notes_out.append({
                            'note': element.nameWithOctave,
                            'pitch': element.pitch.midi,
                            'start': start, 'end': end,
                            'duration': dur, 'velocity': vel,
                        })
                    except Exception:
                        continue

                elif isinstance(element, chord.Chord):
                    try:
                        start = round(float(element.offset) * spq, 3)
                        dur   = round(float(element.duration.quarterLength) * spq, 3)
                        end   = round(start + dur, 3)
                        for n in element.notes:
                            vel = int(n.volume.velocity) if n.volume.velocity else 64
                            notes_out.append({
                                'note': n.nameWithOctave,
                                'pitch': n.pitch.midi,
                                'start': start, 'end': end,
                                'duration': dur, 'velocity': vel,
                            })
                    except Exception:
                        continue

        notes_out.sort(key=lambda x: (x['start'], x['pitch']))
        return notes_out

    except Exception as e:
        print(f"[모듈 1 오류] MusicXML 파싱 실패: {e}")
        return []


# ─────────────────────────────────────────────
# 4. BPM 추출
# ─────────────────────────────────────────────

def _read_bpm_from_xml(xml_path):
    try:
        score = converter.parse(xml_path)
        for el in score.flatten():
            if isinstance(el, tempo.MetronomeMark) and el.number is not None:
                return float(el.number)
    except Exception:
        pass
    try:
        tree = ET.parse(xml_path)
        for sound in tree.getroot().iter('sound'):
            if sound.get('tempo'):
                return float(sound.get('tempo'))
    except Exception:
        pass
    return None


def get_sheet_bpm(sheet_path):
    """
    악보 파일에서 BPM 추출.
    XML/MIDI: 직접 파싱.
    이미지/PDF: Claude Vision 호출 없이 None 반환
               (extract_notes_from_sheet 내부에서 BPM이 결정됨).
    """
    if not os.path.exists(sheet_path):
        return None

    ext = os.path.splitext(sheet_path)[1].lower()

    if ext in ('.xml', '.musicxml', '.mxl'):
        return _read_bpm_from_xml(sheet_path)

    if ext in ('.mid', '.midi'):
        try:
            score = converter.parse(sheet_path)
            for el in score.flatten():
                if isinstance(el, tempo.MetronomeMark) and el.number:
                    return float(el.number)
        except Exception:
            pass

    return None  # 이미지/PDF는 None → quantize 비활성


# ─────────────────────────────────────────────
# 5. MXL 압축 해제
# ─────────────────────────────────────────────

def _extract_mxl(mxl_path, out_xml_path):
    with zipfile.ZipFile(mxl_path, 'r') as z:
        names = z.namelist()
        root_file = None

        if 'META-INF/container.xml' in names:
            try:
                container = ET.fromstring(z.read('META-INF/container.xml'))
                rf = (
                    container.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
                    or container.find('.//rootfile')
                )
                if rf is not None:
                    root_file = rf.get('full-path')
            except Exception:
                pass

        if root_file is None:
            for name in names:
                if name.endswith('.xml') and 'META-INF' not in name:
                    root_file = name
                    break

        if root_file is None:
            raise ValueError(f".mxl 안에 XML 없음: {mxl_path}")

        with z.open(root_file) as src, open(out_xml_path, 'wb') as dst:
            dst.write(src.read())


# ─────────────────────────────────────────────
# 6. PDF → 이미지 변환
# ─────────────────────────────────────────────

def _pdf_to_images(pdf_path, output_dir, dpi=200):
    """PDF를 페이지별 PNG로 변환."""
    try:
        from pdf2image import convert_from_path

        os.makedirs(output_dir, exist_ok=True)
        pages = convert_from_path(pdf_path, dpi=dpi)
        paths = []
        for i, page in enumerate(pages):
            path = os.path.join(output_dir, f'page_{i:03d}.png')
            page.save(path, 'PNG')
            paths.append(path)
        print(f"-> PDF {len(pages)}페이지 변환 완료")
        return paths

    except ImportError:
        print("[모듈 1 오류] pdf2image 없음 → pip install pdf2image")
        print("              poppler:  brew install poppler  (macOS)")
        return []
    except Exception as e:
        print(f"[모듈 1 오류] PDF 변환 실패: {e}")
        return []


# ─────────────────────────────────────────────
# 7. 메인 분기 함수
# ─────────────────────────────────────────────

# 이미지/PDF OMR 처리 시 감지된 BPM을 캐시 (main.py에서 활용 가능)
_last_detected_bpm = None


def extract_notes_from_sheet(sheet_path, fallback_bpm=120):
    """
    파일 형식을 자동 감지해 음표 리스트를 반환.

    - XML / MusicXML / MXL / MIDI : music21 파싱
    - JPEG / PNG / BMP / TIFF     : Claude Vision API
    - PDF                         : 페이지별 이미지 → Claude Vision

    Returns:
        list[dict]: {'note', 'pitch', 'start', 'end', 'duration', 'velocity'}
    """
    global _last_detected_bpm

    if not os.path.exists(sheet_path):
        print(f"[모듈 1 오류] 파일 없음: {sheet_path}")
        return []

    ext = os.path.splitext(sheet_path)[1].lower()

    # ── XML / MusicXML ────────────────────────
    if ext in ('.xml', '.musicxml'):
        print("-> MusicXML 파일 감지")
        return extract_notes_from_musicxml(sheet_path)

    # ── MXL (압축 MusicXML) ───────────────────
    if ext == '.mxl':
        print("-> MXL 파일 감지 → 압축 해제")
        tmp = sheet_path + '.unpacked.xml'
        try:
            _extract_mxl(sheet_path, tmp)
            notes = extract_notes_from_musicxml(tmp)
            _safe_remove(tmp)
            return notes
        except Exception as e:
            print(f"[모듈 1 오류] MXL 압축 해제 실패: {e}")
            return []

    # ── MIDI ──────────────────────────────────
    if ext in ('.mid', '.midi'):
        print("-> MIDI 파일 감지")
        try:
            score = converter.parse(sheet_path)
            tmp = os.path.join(tempfile.gettempdir(), '_midi_conv.musicxml')
            score.write('musicxml', fp=tmp)
            notes = extract_notes_from_musicxml(tmp)
            _safe_remove(tmp)
            return notes
        except Exception as e:
            print(f"[모듈 1 오류] MIDI 변환 실패: {e}")
            return []

    # ── 이미지 ────────────────────────────────
    if ext in ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'):
        print("-> 이미지 파일 감지 → Claude Vision 분석 시작")
        notes, bpm = _image_to_notes_via_claude(sheet_path, fallback_bpm)
        _last_detected_bpm = bpm
        return notes

    # ── PDF ───────────────────────────────────
    if ext == '.pdf':
        print("-> PDF 파일 감지 → 페이지별 Claude Vision 분석 시작")
        return _process_pdf(sheet_path, fallback_bpm)

    print(f"[모듈 1 오류] 지원하지 않는 형식: {ext}")
    print("              지원: .xml .musicxml .mxl .mid .midi .jpg .jpeg .png .pdf")
    return []


def get_last_detected_bpm():
    """
    이미지/PDF 처리 시 Claude Vision이 감지한 BPM을 반환.
    main.py에서 sheet_bpm이 None일 때 활용.
    """
    return _last_detected_bpm


# ─────────────────────────────────────────────
# 8. 내부 헬퍼
# ─────────────────────────────────────────────

def _process_pdf(pdf_path, fallback_bpm=120):
    """PDF 전체를 페이지별로 처리해 음표 리스트 반환."""
    global _last_detected_bpm

    PAGE_GAP_SEC = 0.5
    work_dir = tempfile.mkdtemp(prefix='pdf_vision_')
    all_notes = []
    page_offset = 0.0
    detected_bpm = fallback_bpm

    try:
        image_paths = _pdf_to_images(pdf_path, output_dir=work_dir, dpi=200)
        if not image_paths:
            return []

        for i, img_path in enumerate(image_paths):
            print(f"\n  [페이지 {i + 1} / {len(image_paths)}]")
            page_notes, page_bpm = _image_to_notes_via_claude(img_path, detected_bpm)

            if not page_notes:
                print(f"  → 페이지 {i + 1} 분석 결과 없음, 건너뜀")
                continue

            # 첫 페이지에서 BPM 결정
            if i == 0:
                detected_bpm = page_bpm

            # 시간 오프셋 적용
            for n in page_notes:
                n['start'] = round(n['start'] + page_offset, 3)
                n['end']   = round(n['end']   + page_offset, 3)

            all_notes.extend(page_notes)
            page_offset = page_notes[-1]['end'] + PAGE_GAP_SEC

        _last_detected_bpm = detected_bpm
        all_notes.sort(key=lambda x: (x['start'], x['pitch']))
        return all_notes

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def _safe_remove(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


# ─────────────────────────────────────────────
# 9. DTW 용 onset 시퀀스 추출
# ─────────────────────────────────────────────

def extract_onset_sequence(sheet_path):
    """DTW 정렬을 위한 onset / pitch 시퀀스 추출."""
    try:
        notes = extract_notes_from_sheet(sheet_path)
        if not notes:
            return np.array([]), np.array([])
        return (
            np.array([n['start'] for n in notes]),
            np.array([n['pitch'] for n in notes])
        )
    except Exception as e:
        print(f"[모듈 1 오류] onset 추출 실패: {e}")
        return np.array([]), np.array([])