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

  Map<String, dynamic> toJson() => {
        'score': score,
        'correct': correct,
        'total': total,
        'missed_count': missedCount,
        'wrong_timing_count': wrongTimingCount,
        'extra_count': extraCount,
        'avg_timing_deviation': avgTimingDeviation,
      };
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

  Map<String, dynamic> toJson() => {
        'overall': overall,
        'pitch': pitch,
        'rhythm': rhythm,
        'timing': timing,
        'tips': tips,
        'encouragement': encouragement,
      };
}

class PracticeRecord {
  final int id;
  final String title;
  final String date;
  final String time;
  final ScoreDetail scoreDetail;
  final Feedback? feedback; // SSE 스트리밍 완료 전까지 null
  final String grade;
  final String lang;
  final String? sessionId; // GET /api/feedback/stream 에 사용 (TTL 5분)

  const PracticeRecord({
    required this.id,
    required this.title,
    required this.date,
    required this.time,
    required this.scoreDetail,
    this.feedback,
    required this.grade,
    required this.lang,
    this.sessionId,
  });

  double get score => scoreDetail.score;

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'date': date,
        'time': time,
        'score_detail': scoreDetail.toJson(),
        'feedback': feedback?.toJson(),
        'grade': grade,
        'lang': lang,
        // sessionId는 TTL 5분이므로 저장하지 않음
      };

  factory PracticeRecord.fromStoredJson(Map<String, dynamic> j) {
    return PracticeRecord(
      id: j['id'] as int,
      title: j['title'] as String,
      date: j['date'] as String,
      time: j['time'] as String,
      scoreDetail: ScoreDetail.fromJson(j['score_detail'] as Map<String, dynamic>),
      feedback: j['feedback'] != null
          ? Feedback.fromJson(j['feedback'] as Map<String, dynamic>)
          : null,
      grade: j['grade'] as String,
      lang: j['lang'] as String,
      sessionId: null,
    );
  }

  PracticeRecord copyWith({Feedback? feedback}) => PracticeRecord(
        id: id,
        title: title,
        date: date,
        time: time,
        scoreDetail: scoreDetail,
        feedback: feedback ?? this.feedback,
        grade: grade,
        lang: lang,
        sessionId: sessionId,
      );

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
      date: '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}',
      time: timeStr,
      scoreDetail: ScoreDetail.fromJson(json['score'] as Map<String, dynamic>),
      feedback: null, // 피드백은 /api/feedback/stream SSE 수신 후 별도 설정
      grade: json['grade'] as String,
      lang: json['lang'] as String,
      sessionId: json['session_id'] as String?,
    );
  }
}
