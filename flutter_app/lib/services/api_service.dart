import 'dart:convert';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;

import '../models/record.dart';

class ApiService {
  static const String _defaultBase = 'http://localhost:8080';

  static String get baseUrl {
    const env = String.fromEnvironment('API_BASE', defaultValue: _defaultBase);
    return env;
  }

  /// POST /api/analyze — 채점만 수행 (GPT 없음)
  /// 반환: PracticeRecord (feedback = null)
  /// 피드백은 FeedbackStreamService.stream() SSE로 별도 수신
  static Future<PracticeRecord> analyze({
    required List<int> sheetBytes,
    required String sheetName,
    required List<int> audioBytes,
    required String audioName,
    required String title,
    required String lang,
  }) async {
    final uri = Uri.parse('$baseUrl/api/analyze');
    final request = http.MultipartRequest('POST', uri);

    request.fields['lang'] = lang;
    request.files.add(http.MultipartFile.fromBytes(
      'sheet',
      sheetBytes,
      filename: sheetName,
    ));
    request.files.add(http.MultipartFile.fromBytes(
      'audio',
      audioBytes,
      filename: audioName,
    ));

    if (!kIsWeb) {
      request.headers['Accept'] = 'application/json';
    }

    final streamed = await request.send().timeout(const Duration(minutes: 6));
    final body = await streamed.stream.bytesToString();

    if (streamed.statusCode != 200) {
      final err = json.decode(body) as Map<String, dynamic>;
      throw Exception(err['error'] ?? '서버 오류 (${streamed.statusCode})');
    }

    final json_ = json.decode(body) as Map<String, dynamic>;
    return PracticeRecord.fromApiResponse(json_, title: title);
  }

  /// GET /health
  static Future<bool> health() async {
    try {
      final res = await http
          .get(Uri.parse('$baseUrl/health'))
          .timeout(const Duration(seconds: 5));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
