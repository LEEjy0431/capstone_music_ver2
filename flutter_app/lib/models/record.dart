class ScoreDetail {
  final double score;
  final int correct;
  final int total;
  final int missedCount;
  final int wrongTimingCount;
  final int extraCount;
  final double avgTimingDeviation;

  const ScoreDetail({
    required this.score,
    required this.correct,
    required this.total,
    required this.missedCount,
    required this.wrongTimingCount,
    required this.extraCount,
    required this.avgTimingDeviation,
  });

  factory ScoreDetail.fromJson(Map<String, dynamic> j) => ScoreDetail(
        score: (j['score'] as num).toDouble(),
        correct: j['correct'] as int,
        total: j['total'] as int,
        missedCount: j['missed_count'] as int,
        wrongTimingCount: j['wrong_timing_count'] as int,
        extraCount: j['extra_count'] as int,
        avgTimingDeviation: (j['avg_timing_deviation'] as num).toDouble(),
      );
}

class Feedback {
  final String overall;
  final String pitch;
  final String rhythm;
  final String timing;
  final List<String> tips;
  final String encouragement;

  const Feedback({
    required this.overall,
    required this.pitch,
    required this.rhythm,
    required this.timing,
    required this.tips,
    required this.encouragement,
  });

  factory Feedback.fromJson(Map<String, dynamic> j) => Feedback(
        overall: j['overall'] as String,
        pitch: j['pitch'] as String,
        rhythm: j['rhythm'] as String,
        timing: j['timing'] as String,
        tips: List<String>.from(j['tips'] as List),
        encouragement: j['encouragement'] as String,
      );
}

class PracticeRecord {
  final int id;
  final String title;
  final String date;
  final String time;
  final ScoreDetail scoreDetail;
  // feedback은 SSE 스트리밍 완료 후 채워진다 (초기값 null)
  final Feedback? feedback;
  final String grade;
  final String lang;

  const PracticeRecord({
    required this.id,
    required this.title,
    required this.date,
    required this.time,
    required this.scoreDetail,
    required this.grade,
    required this.lang,
    this.feedback,
  });

  double get score => scoreDetail.score;

  PracticeRecord copyWith({Feedback? feedback}) => PracticeRecord(
        id: id,
        title: title,
        date: date,
        time: time,
        scoreDetail: scoreDetail,
        grade: grade,
        lang: lang,
        feedback: feedback ?? this.feedback,
      );

  /// /api/analyze 응답 파싱 — score + grade + lang 만 반환됨
  /// feedback은 null, SSE done 이벤트 수신 후 copyWith으로 채운다
  factory PracticeRecord.fromApiResponse(
    Map<String, dynamic> json, {
    required String title,
  }) {
    final now = DateTime.now();
    final hour = now.hour;
    final period = hour < 12 ? '오전' : '오후';
    final h = hour % 12 == 0 ? 12 : hour % 12;
    final timeStr = '$period $h:${now.minute.toString().padLeft(2, '0')}';

    return PracticeRecord(
      id: now.millisecondsSinceEpoch,
      title: title,
      date:
          '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}',
      time: timeStr,
      scoreDetail: ScoreDetail.fromJson(json['score'] as Map<String, dynamic>),
      feedback: null,
      grade: json['grade'] as String,
      lang: json['lang'] as String,
    );
  }
}
