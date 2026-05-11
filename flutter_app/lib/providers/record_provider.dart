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
}
