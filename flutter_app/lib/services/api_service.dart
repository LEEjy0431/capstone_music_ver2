import 'dart:convert';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;

import '../models/record.dart';

class ApiService {
  static const String _defaultBase = 'http://localhost:8080';

  static String get baseUrl {
    // dart-define으로 주입: --dart-define=API_BASE=http://...
    const env = String.fromEnvironment('API_BASE', defaultValue: _defaultBase);
    return env;
  }

  /// POST /api/analyze — multipart upload (sheet + audio + lang)
  /// [sheetBytes] / [audioBytes]: web에서는 Uint8List, Android에서도 동일
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

    // 웹 환경에서는 CORS preflight가 자동으로 처리됨
    if (!kIsWeb) {
      request.headers['Accept'] = 'application/json';
    }

    final streamed = await request.send().timeout(const Duration(minutes: 3));
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
