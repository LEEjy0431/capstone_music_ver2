import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/record.dart';

class StorageService {
  static const _key = 'practice_records';

  static Future<List<PracticeRecord>> loadRecords() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null) return [];
    try {
      final list = json.decode(raw) as List<dynamic>;
      return list
          .map((e) => PracticeRecord.fromStoredJson(e as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  static Future<void> saveRecords(List<PracticeRecord> records) async {
    final prefs = await SharedPreferences.getInstance();
    final encoded = json.encode(records.map((r) => r.toJson()).toList());
    await prefs.setString(_key, encoded);
  }
}
