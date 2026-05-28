import 'package:flutter/foundation.dart';

import '../models/record.dart';
import '../services/api_service.dart';

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

  /// POST /api/analyze 호출 — 채점 결과와 session_id를 포함한 레코드를 반환한다.
  /// GPT 피드백은 포함되지 않으며, updateFeedback() 으로 별도 설정한다.
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
  void updateFeedback(int id, Feedback feedback) {
    final index = _records.indexWhere((r) => r.id == id);
    if (index == -1) return;
    _records[index] = _records[index].copyWith(feedback: feedback);
    notifyListeners();
  }
}
