import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/record.dart';
import 'api_service.dart';

/// SSE 이벤트 타입
enum FeedbackEventType { chunk, done, error }

/// 서버에서 수신하는 단일 SSE 이벤트
class FeedbackEvent {
  final FeedbackEventType type;
  final String? text;          // chunk: GPT 텍스트 조각
  final Feedback? feedback;    // done: 완성된 피드백
  final String? error;         // error: 오류 메시지

  const FeedbackEvent({
    required this.type,
    this.text,
    this.feedback,
    this.error,
  });

  factory FeedbackEvent.fromJson(Map<String, dynamic> j) {
    final type = switch (j['type'] as String) {
      'chunk' => FeedbackEventType.chunk,
      'done' => FeedbackEventType.done,
      _ => FeedbackEventType.error,
    };

    return FeedbackEvent(
      type: type,
      text: j['text'] as String?,
      feedback: j['feedback'] != null
          ? Feedback.fromJson(j['feedback'] as Map<String, dynamic>)
          : null,
      error: j['error'] as String?,
    );
  }
}

/// GET /api/feedback/stream 으로 SSE를 수신하는 서비스
///
/// 사용 예:
/// ```dart
/// final buffer = StringBuffer();
/// await for (final event in FeedbackStreamService.stream(score: s, lang: 'ko')) {
///   if (event.type == FeedbackEventType.chunk) {
///     buffer.write(event.text);
///     setState(() => _streamText = buffer.toString());
///   } else if (event.type == FeedbackEventType.done) {
///     setState(() => _feedback = event.feedback);
///   }
/// }
/// ```
class FeedbackStreamService {
  static Stream<FeedbackEvent> stream({
    required ScoreDetail score,
    required String lang,
  }) async* {
    final uri = Uri.parse('${ApiService.baseUrl}/api/feedback/stream').replace(
      queryParameters: {
        'score': score.score.toString(),
        'correct': score.correct.toString(),
        'total': score.total.toString(),
        'missed': score.missedCount.toString(),
        'timing_errors': score.wrongTimingCount.toString(),
        'extra': score.extraCount.toString(),
        'avg_dev': score.avgTimingDeviation.toString(),
        'lang': lang,
      },
    );

    final client = http.Client();
    try {
      final request = http.Request('GET', uri);
      request.headers['Accept'] = 'text/event-stream';
      request.headers['Cache-Control'] = 'no-cache';

      final response = await client.send(request);

      if (response.statusCode != 200) {
        yield FeedbackEvent(
          type: FeedbackEventType.error,
          error: '서버 오류 (${response.statusCode})',
        );
        return;
      }

      // SSE 스트림 파싱
      // 형식: "event: chunk\ndata: {...}\n\n"
      final buffer = StringBuffer();

      await for (final chunk
          in response.stream.transform(utf8.decoder)) {
        buffer.write(chunk);
        final raw = buffer.toString();

        // 완성된 이벤트 블록 (\n\n 로 구분)
        final blocks = raw.split('\n\n');
        // 마지막 미완성 블록은 다음 청크를 기다림
        buffer
          ..clear()
          ..write(blocks.last);

        for (final block in blocks.sublist(0, blocks.length - 1)) {
          if (block.trim().isEmpty || block.startsWith(':')) continue;

          // "event: ...\ndata: ..." 파싱
          String? dataLine;
          for (final line in block.split('\n')) {
            if (line.startsWith('data: ')) {
              dataLine = line.substring(6);
            }
          }

          if (dataLine == null || dataLine.isEmpty) continue;

          try {
            final json_ =
                jsonDecode(dataLine) as Map<String, dynamic>;
            final event = FeedbackEvent.fromJson(json_);
            yield event;

            if (event.type == FeedbackEventType.done ||
                event.type == FeedbackEventType.error) {
              return;
            }
          } catch (_) {
            // 파싱 실패한 청크는 무시
          }
        }
      }
    } finally {
      client.close();
    }
  }
}
