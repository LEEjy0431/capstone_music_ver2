import 'package:flutter/foundation.dart';

import '../models/record.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';

class RecordProvider extends ChangeNotifier {
  final List<PracticeRecord> _records = [];
  bool _analyzing = false;
  String? _error;

  List<PracticeRecord> get records => List.unmodifiable(_records);
  bool get analyzing => _analyzing;
  String? get error => _error;

  double get averageScore {
    if (_records.isEmpty) return 0;
    return _records.map((r) => r.score).reduce((a, b) => a + b) /
        _records.length;
  }

  double get highestScore {
    if (_records.isEmpty) return 0;
    return _records.map((r) => r.score).reduce((a, b) => a > b ? a : b);
  }

  /// 앱 시작 시 로컬 저장 기록을 불러온다.
  Future<void> init() async {
    final saved = await StorageService.loadRecords();
    _records.addAll(saved);
    notifyListeners();
  }

  Future<void> _save() async {
    await StorageService.saveRecords(_records);
  }

  /// POST /api/analyze 호출 — 채점 결과와 session_id를 포함한 레코드를 반환한다.
  Future<PracticeRecord?> analyze({
    required List<int> sheetBytes,
    required String sheetName,
    required List<int> audioBytes,
    required String audioName,
    required String title,
    required String lang,
  }) async {
    _analyzing = true;
    _error = null;
    notifyListeners();

    try {
      final record = await ApiService.analyze(
        sheetBytes: sheetBytes,
        sheetName: sheetName,
        audioBytes: audioBytes,
        audioName: audioName,
        title: title,
        lang: lang,
      );
      _records.insert(0, record);
      await _save();
      return record;
    } catch (e) {
      _error = e.toString().replaceFirst('Exception: ', '');
      return null;
    } finally {
      _analyzing = false;
      notifyListeners();
    }
  }

  /// SSE 스트리밍 완료 후 특정 레코드에 피드백을 설정한다.
  Future<void> updateFeedback(int id, Feedback feedback) async {
    final index = _records.indexWhere((r) => r.id == id);
    if (index == -1) return;
    _records[index] = _records[index].copyWith(feedback: feedback);
    await _save();
    notifyListeners();
  }

  /// 특정 기록을 삭제한다.
  Future<void> deleteRecord(int id) async {
    _records.removeWhere((r) => r.id == id);
    await _save();
    notifyListeners();
  }
}
