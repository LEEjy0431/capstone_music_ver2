from music21 import converter, note, chord, tempo
import xml.etree.ElementTree as ET
import numpy as np
import glob
import os
import re
import shutil
import subprocess
import tempfile
import zipfile


# ─────────────────────────────────────────────────────────────────
# 이미지/PDF 처리 시 감지된 BPM 캐시
# ─────────────────────────────────────────────────────────────────
_last_detected_bpm: float | None = None


# ═════════════════════════════════════════════════════════════════
# 1. 공통 유틸리티
# ═════════════════════════════════════════════════════════════════

def _safe_remove(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _needs_ascii_copy(path: str) -> bool:
    try:
        path.encode('ascii')
        return ' ' in path  # 공백도 Java에서 문제될 수 있음
    except UnicodeEncodeError:
        return True  # 한글 등 포함


def _copy_to_ascii_temp(src_path: str, suffix: str = '') -> str:
    ext = os.path.splitext(src_path)[1]
    fd, dst_path = tempfile.mkstemp(suffix=suffix or ext, prefix='omr_input_')
    os.close(fd)
    shutil.copy2(src_path, dst_path)
    return dst_path


# ═════════════════════════════════════════════════════════════════
# 2. Audiveris OMR  (1순위)
# ═════════════════════════════════════════════════════════════════

# macOS .app 내부 실행 파일 경로 후보 목록
_AUDIVERIS_CANDIDATES = [
    'audiveris',                                           # PATH에 등록된 경우
    '/Applications/Audiveris.app/Contents/MacOS/audiveris',  # macOS 기본 설치 위치
    os.path.expanduser('~/Applications/Audiveris.app/Contents/MacOS/audiveris'),
]


def _find_audiveris() -> str | None:
    """Audiveris 실행 파일 경로 탐색. 없으면 None."""
    for candidate in _AUDIVERIS_CANDIDATES:
        if shutil.which(candidate) or os.path.isfile(candidate):
            return candidate
    return None


def _image_to_notes_via_audiveris(
    image_path: str,
    fallback_bpm: float = 120,
    timeout_sec: int = 300,
) -> tuple[list[dict], float | None]:
    """
    Audiveris CLI로 악보 이미지/PDF → MusicXML(.mxl) → 음표 변환.

    처리 흐름:
      1) 한글/공백 경로면 ASCII 임시 경로로 복사
      2) audiveris -batch -export -output <tmp_dir> <image>
      3) 출력된 .mxl 파일을 music21로 파싱

    Returns:
        (notes, bpm) 또는 실패 시 ([], None)
    """
    audiveris_bin = _find_audiveris()
    if audiveris_bin is None:
        print("[Audiveris] 실행 파일을 찾을 수 없습니다.")
        print("  설치: https://github.com/Audiveris/audiveris/releases")
        print("  설치 후 /Applications/Audiveris.app 에 위치해야 합니다.")
        return [], None

    # ── ASCII 경로 보장 ───────────────────────────────────────
    ascii_copy_path = None
    if _needs_ascii_copy(image_path):
        ext = os.path.splitext(image_path)[1]
        ascii_copy_path = _copy_to_ascii_temp(image_path, suffix=ext)
        input_path = ascii_copy_path
        print(f"   (한글/공백 경로 감지 → ASCII 임시 경로로 복사)")
    else:
        input_path = image_path

    out_dir = tempfile.mkdtemp(prefix='audiveris_out_')

    try:
        cmd = [
            audiveris_bin,
            '-batch',       # GUI 없이 실행
            '-export',      # MusicXML 내보내기 (-transcribe 자동 포함)
            '-output', out_dir,
            '--',           # 이후는 입력 파일
            input_path,
        ]

        print(f"-> Audiveris 분석 중: {os.path.basename(image_path)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )

        # 출력 파일 탐색 (.mxl 또는 .xml, 하위 폴더 포함)
        mxl_files = (
            glob.glob(os.path.join(out_dir, '**', '*.mxl'), recursive=True)
            + glob.glob(os.path.join(out_dir, '**', '*.xml'), recursive=True)
            + glob.glob(os.path.join(out_dir, '**', '*.musicxml'), recursive=True)
        )

        if not mxl_files:
            # stderr 에서 오류 힌트 추출
            stderr = result.stderr or ''
            _print_audiveris_error_hint(stderr)
            return [], None

        # 가장 큰 파일 선택 (내용이 많은 것)
        mxl_path = max(mxl_files, key=os.path.getsize)
        notes = extract_notes_from_musicxml(mxl_path)
        bpm   = _read_bpm_from_xml(mxl_path) or fallback_bpm

        print(f"-> Audiveris 완료: {len(notes)}개 음표, BPM={bpm}")
        return notes, bpm

    except subprocess.TimeoutExpired:
        print(f"[Audiveris] 타임아웃 ({timeout_sec}s). 이미지가 너무 크거나 복잡합니다.")
        return [], None
    except Exception as e:
        print(f"[Audiveris] 오류: {e}")
        return [], None
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
        if ascii_copy_path:
            _safe_remove(ascii_copy_path)


def _print_audiveris_error_hint(stderr: str) -> None:
    """Audiveris stderr 메시지를 분석해 힌트 출력."""
    if 'Could not find file' in stderr:
        print("[Audiveris] 파일을 찾지 못했습니다.")
        print("  → 경로에 한글/공백이 있어도 자동 처리되어야 하는데 실패했습니다.")
        print("  → 파일을 /tmp/sheet.png 처럼 간단한 경로로 직접 복사 후 시도해보세요.")
    elif 'No installed OCR' in stderr:
        print("[Audiveris] OCR 언어팩 미설치 (음표 인식에는 영향 적음)")
        print("  → 빠르기말 등 텍스트가 누락될 수 있습니다.")
        print("  → 설치: brew install tesseract tesseract-lang")
    elif 'OutOfMemoryError' in stderr:
        print("[Audiveris] 메모리 부족. 이미지 해상도를 낮추거나 JVM 메모리를 늘려주세요.")
    elif stderr.strip():
        # 마지막 오류 줄만 출력 (너무 길면 잘라냄)
        last_lines = [l for l in stderr.strip().splitlines() if l.strip()][-3:]
        print(f"[Audiveris] 변환 실패:\n  " + "\n  ".join(last_lines))
    else:
        print("[Audiveris] 변환 실패: 출력 파일이 생성되지 않았습니다.")


# ═════════════════════════════════════════════════════════════════
# 3. oemer OMR  (2순위 fallback)
# ═════════════════════════════════════════════════════════════════

def _patch_numpy_compat() -> None:
    """oemer가 사용하는 deprecated NumPy 별칭을 메모리에서 복원."""
    import warnings
    import numpy as _np
    for name, builtin in [('int', int), ('float', float), ('bool', bool),
                          ('complex', complex), ('object', object), ('str', str)]:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            try:
                setattr(_np, name, builtin)
            except Exception:
                pass


def _is_oemer_available() -> bool:
    try:
        import importlib
        return importlib.util.find_spec('oemer') is not None
    except Exception:
        return False


def _image_to_notes_via_oemer(
    image_path: str,
    fallback_bpm: float = 120,
    deskew: bool = True,
) -> tuple[list[dict], float | None]:
    """
    oemer Python API로 악보 이미지 → 음표 변환 (Audiveris fallback).
    numpy 호환성 패치를 자동 적용.
    """
    if not _is_oemer_available():
        print("[oemer] 미설치 (pip install oemer)")
        return [], None

    _patch_numpy_compat()

    out_dir = tempfile.mkdtemp(prefix='oemer_out_')
    try:
        from oemer.ete import extract as oemer_extract

        class _SafeNamespace:
            """oemer 버전별 인자 차이를 흡수. 없는 속성은 False 반환."""
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
            def __getattr__(self, _):
                return False

        args = _SafeNamespace(
            img_path=os.path.abspath(image_path),
            output_path=out_dir,
            save_cache=False,
            use_cache=False,
            without_deskew=not deskew,
            use_tf=False,
        )

        print(f"-> oemer 분석 중: {os.path.basename(image_path)}")
        mxl_path = oemer_extract(args)

        if not mxl_path or not os.path.exists(str(mxl_path)):
            candidates = (
                glob.glob(os.path.join(out_dir, '*.xml'))
                + glob.glob(os.path.join(out_dir, '*.musicxml'))
                + glob.glob(os.path.join(out_dir, '*.mxl'))
            )
            if not candidates:
                print("[oemer] 출력 파일 없음")
                return [], None
            mxl_path = candidates[0]

        notes = extract_notes_from_musicxml(str(mxl_path))
        bpm   = _read_bpm_from_xml(str(mxl_path)) or fallback_bpm
        print(f"-> oemer 완료: {len(notes)}개 음표, BPM={bpm}")
        return notes, bpm

    except Exception as e:
        print(f"[oemer] 오류: {e}")
        return [], None
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


# ═════════════════════════════════════════════════════════════════
# 4. 이미지 통합 처리  (Audiveris → oemer fallback)
# ═════════════════════════════════════════════════════════════════

def _image_to_notes(
    image_path: str,
    fallback_bpm: float = 120,
    deskew: bool = True,
    audiveris_timeout: int = 300,
) -> tuple[list[dict], float]:
    """
    단일 이미지 → 음표 추출.
    1순위: Audiveris (설치된 경우)
    2순위: oemer
    """
    # 1순위: Audiveris
    if _find_audiveris():
        notes, bpm = _image_to_notes_via_audiveris(
            image_path,
            fallback_bpm=fallback_bpm,
            timeout_sec=audiveris_timeout,
        )
        if notes:
            return notes, bpm if bpm is not None else fallback_bpm
        print("-> Audiveris 실패, oemer fallback 시도...")
    else:
        print("-> Audiveris 미설치, oemer로 시도...")

    # 2순위: oemer
    notes, bpm = _image_to_notes_via_oemer(
        image_path,
        fallback_bpm=fallback_bpm,
        deskew=deskew,
    )
    return notes, bpm if bpm is not None else fallback_bpm


# ═════════════════════════════════════════════════════════════════
# 5. MusicXML / music21 파싱
# ═════════════════════════════════════════════════════════════════

def extract_notes_from_musicxml(xml_path: str) -> list[dict]:
    """MusicXML(.xml / .mxl) 파일에서 음표 데이터를 초(seconds) 단위로 추출."""
    try:
        score = converter.parse(xml_path)

        bpm = 120.0
        for element in score.flatten():
            if isinstance(element, tempo.MetronomeMark) and element.number is not None:
                bpm = float(element.number)
                break

        # XML 직접 파싱으로 BPM 재확인 (.xml 한정)
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
                            'note':     element.nameWithOctave,
                            'pitch':    element.pitch.midi,
                            'start':    start,
                            'end':      end,
                            'duration': dur,
                            'velocity': vel,
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
                                'note':     n.nameWithOctave,
                                'pitch':    n.pitch.midi,
                                'start':    start,
                                'end':      end,
                                'duration': dur,
                                'velocity': vel,
                            })
                    except Exception:
                        continue

        # ── 후처리: 꾸밈음 제거 + 중복 제거 ──────────────────
        # 1) duration=0 제거: grace note (꾸밈음/앞꾸밈음)은 오디오에서
        #    검출 불가능하므로 채점 대상에서 제외
        before = len(notes_out)
        notes_out = [n for n in notes_out if n['duration'] > 0.0]
        grace_removed = before - len(notes_out)
        if grace_removed:
            print(f"-> 꾸밈음(grace note) {grace_removed}개 제외")

        # 2) 중복 제거: 같은 (pitch, start) 쌍이 여러 목소리(voice)에서
        #    중복 추출되는 현상 방지. 앞쪽 것만 유지.
        seen: set[tuple] = set()
        deduped = []
        for n in notes_out:
            key = (n['pitch'], n['start'])
            if key not in seen:
                seen.add(key)
                deduped.append(n)
        dup_removed = len(notes_out) - len(deduped)
        if dup_removed:
            print(f"-> 중복 음표 {dup_removed}개 제거")
        notes_out = deduped

        notes_out.sort(key=lambda x: (x['start'], x['pitch']))
        print(f"-> 최종 음표 수: {len(notes_out)}개")
        return notes_out

    except Exception as e:
        print(f"[모듈 1 오류] MusicXML 파싱 실패: {e}")
        return []


# ═════════════════════════════════════════════════════════════════
# 6. BPM 추출
# ═════════════════════════════════════════════════════════════════

def _read_bpm_from_xml(xml_path: str) -> float | None:
    """XML / MXL 파일에서 BPM 추출. 못 찾으면 None."""
    try:
        score = converter.parse(xml_path)
        for el in score.flatten():
            if isinstance(el, tempo.MetronomeMark) and el.number is not None:
                return float(el.number)
    except Exception:
        pass
    # .xml 이면 ET로 직접 재시도
    if xml_path.endswith(('.xml', '.musicxml')):
        try:
            tree = ET.parse(xml_path)
            for sound in tree.getroot().iter('sound'):
                if sound.get('tempo'):
                    return float(sound.get('tempo'))
        except Exception:
            pass
    return None


def get_sheet_bpm(sheet_path: str) -> float | None:
    """
    악보 파일에서 BPM 추출.
    이미지/PDF는 None 반환 → extract_notes_from_sheet 내부에서 결정.
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
    return None


def get_last_detected_bpm() -> float | None:
    """이미지/PDF OMR 처리 시 감지된 BPM 반환 (main.py에서 활용)."""
    return _last_detected_bpm


# ═════════════════════════════════════════════════════════════════
# 7. MXL 압축 해제
# ═════════════════════════════════════════════════════════════════

def _extract_mxl(mxl_path: str, out_xml_path: str) -> None:
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


# ═════════════════════════════════════════════════════════════════
# 8. PDF → 이미지 변환 (oemer fallback용)
# ═════════════════════════════════════════════════════════════════

def _pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 200) -> list[str]:
    try:
        from pdf2image import convert_from_path
        os.makedirs(output_dir, exist_ok=True)
        pages = convert_from_path(pdf_path, dpi=dpi)
        paths = []
        for i, page in enumerate(pages):
            path = os.path.join(output_dir, f'page_{i:03d}.png')
            page.save(path, 'PNG')
            paths.append(path)
        print(f"-> PDF {len(pages)}페이지 → PNG 변환 완료")
        return paths
    except ImportError:
        print("[모듈 1 오류] pdf2image 없음 → pip install pdf2image")
        print("              macOS: brew install poppler")
        return []
    except Exception as e:
        print(f"[모듈 1 오류] PDF 변환 실패: {e}")
        return []


# ═════════════════════════════════════════════════════════════════
# 9. PDF 처리
# ═════════════════════════════════════════════════════════════════

def _process_pdf(
    pdf_path: str,
    fallback_bpm: float = 120,
    deskew: bool = True,
    audiveris_timeout: int = 300,
) -> list[dict]:
    global _last_detected_bpm

    # ── Audiveris: PDF 직접 처리 (페이지 분할 불필요) ───────────
    if _find_audiveris():
        print("-> Audiveris가 PDF를 직접 처리합니다 (페이지 자동 분할)")
        notes, bpm = _image_to_notes_via_audiveris(
            pdf_path,
            fallback_bpm=fallback_bpm,
            timeout_sec=audiveris_timeout,
        )
        if notes:
            _last_detected_bpm = bpm
            return notes
        print("-> Audiveris PDF 처리 실패, oemer fallback (페이지별)...")

    # ── oemer fallback: 페이지별 PNG 변환 후 처리 ───────────────
    PAGE_GAP_SEC = 0.5
    work_dir = tempfile.mkdtemp(prefix='pdf_omr_')
    all_notes: list[dict] = []
    page_offset = 0.0
    detected_bpm = fallback_bpm

    try:
        image_paths = _pdf_to_images(pdf_path, output_dir=work_dir, dpi=200)
        if not image_paths:
            return []

        for i, img_path in enumerate(image_paths):
            print(f"\n  [페이지 {i + 1} / {len(image_paths)}]")
            page_notes, page_bpm = _image_to_notes_via_oemer(
                img_path, fallback_bpm=detected_bpm, deskew=deskew,
            )
            if not page_notes:
                print(f"  -> 페이지 {i + 1} 인식 실패, 건너뜀")
                continue
            if i == 0 and page_bpm is not None:
                detected_bpm = page_bpm
            for n in page_notes:
                n['start'] = round(n['start'] + page_offset, 3)
                n['end']   = round(n['end']   + page_offset, 3)
            all_notes.extend(page_notes)
            page_offset = all_notes[-1]['end'] + PAGE_GAP_SEC

        _last_detected_bpm = detected_bpm
        all_notes.sort(key=lambda x: (x['start'], x['pitch']))
        return all_notes
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


# ═════════════════════════════════════════════════════════════════
# 10. 메인 분기 함수 (공개 API)
# ═════════════════════════════════════════════════════════════════

def _log_omr_strategy() -> None:
    """현재 사용할 OMR 엔진 출력."""
    audiveris = _find_audiveris()
    oemer_ok  = _is_oemer_available()
    if audiveris:
        print(f"   OMR 전략: Audiveris (1순위) → {'oemer' if oemer_ok else '없음'} (fallback)")
    elif oemer_ok:
        print("   OMR 전략: oemer (Audiveris 미설치)")
        print("   Audiveris 설치 권장: https://github.com/Audiveris/audiveris/releases")
    else:
        print("   [경고] Audiveris / oemer 모두 미설치 → 악보 인식 불가")
        print("   Audiveris: https://github.com/Audiveris/audiveris/releases")
        print("   oemer:     pip install oemer")


def extract_notes_from_sheet(
    sheet_path: str,
    fallback_bpm: float = 120,
    deskew: bool = True,
    audiveris_timeout: int = 300,
) -> list[dict]:
    """
    파일 형식을 자동 감지해 음표 리스트 반환.

    Args:
        sheet_path:        악보 파일 경로 (한글/공백 경로 자동 처리)
        fallback_bpm:      BPM 감지 실패 시 기본값
        deskew:            oemer 기울기 보정 여부
        audiveris_timeout: Audiveris 최대 대기 시간(초)

    Returns:
        list[dict]: {'note', 'pitch', 'start', 'end', 'duration', 'velocity'}
    """
    global _last_detected_bpm

    if not os.path.exists(sheet_path):
        print(f"[모듈 1 오류] 파일 없음: {sheet_path}")
        return []

    ext = os.path.splitext(sheet_path)[1].lower()

    # ── MusicXML ─────────────────────────────────────────────────
    if ext in ('.xml', '.musicxml'):
        print("-> MusicXML 파일 감지")
        return extract_notes_from_musicxml(sheet_path)

    # ── MXL (압축 MusicXML) ──────────────────────────────────────
    if ext == '.mxl':
        print("-> MXL 파일 감지 → 압축 해제")
        tmp = sheet_path + '.unpacked.xml'
        try:
            _extract_mxl(sheet_path, tmp)
            return extract_notes_from_musicxml(tmp)
        except Exception as e:
            print(f"[모듈 1 오류] MXL 압축 해제 실패: {e}")
            return []
        finally:
            _safe_remove(tmp)

    # ── MIDI ─────────────────────────────────────────────────────
    if ext in ('.mid', '.midi'):
        print("-> MIDI 파일 감지")
        tmp = os.path.join(tempfile.gettempdir(), '_midi_conv.musicxml')
        try:
            score = converter.parse(sheet_path)
            score.write('musicxml', fp=tmp)
            return extract_notes_from_musicxml(tmp)
        except Exception as e:
            print(f"[모듈 1 오류] MIDI 변환 실패: {e}")
            return []
        finally:
            _safe_remove(tmp)

    # ── 이미지 ───────────────────────────────────────────────────
    if ext in ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'):
        print("-> 이미지 파일 감지")
        _log_omr_strategy()
        notes, bpm = _image_to_notes(
            sheet_path,
            fallback_bpm=fallback_bpm,
            deskew=deskew,
            audiveris_timeout=audiveris_timeout,
        )
        _last_detected_bpm = bpm
        return notes

    # ── PDF ──────────────────────────────────────────────────────
    if ext == '.pdf':
        print("-> PDF 파일 감지")
        _log_omr_strategy()
        return _process_pdf(
            sheet_path,
            fallback_bpm=fallback_bpm,
            deskew=deskew,
            audiveris_timeout=audiveris_timeout,
        )

    print(f"[모듈 1 오류] 지원하지 않는 형식: {ext}")
    print("              지원: .xml .musicxml .mxl .mid .midi .jpg .jpeg .png .bmp .tiff .pdf")
    return []


# ═════════════════════════════════════════════════════════════════
# 11. DTW 용 onset 시퀀스 추출
# ═════════════════════════════════════════════════════════════════

def extract_onset_sequence(sheet_path: str) -> tuple[np.ndarray, np.ndarray]:
    """DTW 정렬을 위한 onset / pitch 시퀀스 추출."""
    try:
        notes = extract_notes_from_sheet(sheet_path)
        if not notes:
            return np.array([]), np.array([])
        return (
            np.array([n['start'] for n in notes]),
            np.array([n['pitch'] for n in notes]),
        )
    except Exception as e:
        print(f"[모듈 1 오류] onset 추출 실패: {e}")
        return np.array([]), np.array([])