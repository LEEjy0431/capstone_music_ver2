import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/record.dart';
import '../providers/record_provider.dart';
import '../services/feedback_stream_service.dart';
import '../theme.dart';
import '../widgets/feedback_card.dart';
import '../widgets/score_bar.dart';

class AnalysisPage extends StatefulWidget {
  const AnalysisPage({super.key});

  @override
  State<AnalysisPage> createState() => _AnalysisPageState();
}

class _AnalysisPageState extends State<AnalysisPage> {
  PlatformFile? _audioFile;
  PlatformFile? _sheetFile;
  String _lang = 'ko';
  PracticeRecord? _result;

  // SSE 스트리밍 상태
  String _streamText = '';         // 누적 텍스트 (청크)
  Feedback? _streamedFeedback;     // done 이벤트 수신 후 완성된 피드백
  bool _streaming = false;

  static const _langs = [
    ('ko', '한국어'),
    ('en', 'English'),
    ('ja', '日本語'),
    ('zh', '中文'),
  ];

  Future<void> _pickFile(bool isAudio) async {
    final ext = isAudio ? ['wav'] : ['xml', 'musicxml'];
    final res = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ext,
      withData: true,
    );
    if (res == null || res.files.isEmpty) return;
    setState(() {
      if (isAudio) {
        _audioFile = res.files.first;
      } else {
        _sheetFile = res.files.first;
      }
    });
  }

  Future<void> _analyze() async {
    if (_audioFile == null || _sheetFile == null) return;
    final provider = context.read<RecordProvider>();

    // 1단계: Python 분석 + 채점 (blocking)
    final record = await provider.analyze(
      sheetBytes: _sheetFile!.bytes!,
      sheetName: _sheetFile!.name,
      audioBytes: _audioFile!.bytes!,
      audioName: _audioFile!.name,
      title: _sheetFile!.name.replaceAll(RegExp(r'\.\w+$'), ''),
      lang: _lang,
    );

    if (record == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(provider.error ?? '분석 실패'),
            backgroundColor: Colors.red,
          ),
        );
      }
      return;
    }

    setState(() {
      _result = record;
      _streamText = '';
      _streamedFeedback = null;
    });

    // 2단계: session_id로 SSE 스트리밍 GPT 피드백 수신
    if (record.sessionId != null) {
      await _streamFeedback(record.sessionId!);
    }
  }

  Future<void> _streamFeedback(String sessionId) async {
    setState(() {
      _streaming = true;
      _streamText = '';
      _streamedFeedback = null;
    });

    final buffer = StringBuffer();

    try {
      await for (final event in FeedbackStreamService.stream(
        sessionId: sessionId,
        lang: _lang,
      )) {
        if (!mounted) break;

        switch (event.type) {
          case FeedbackEventType.chunk:
            buffer.write(event.text ?? '');
            setState(() => _streamText = buffer.toString());

          case FeedbackEventType.done:
            setState(() {
              _streamedFeedback = event.feedback;
              _streaming = false;
            });
            if (event.feedback != null && _result != null) {
              context.read<RecordProvider>().updateFeedback(
                    _result!.id,
                    event.feedback!,
                  );
            }

          case FeedbackEventType.error:
            setState(() => _streaming = false);
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('피드백 오류: ${event.error}'),
                  backgroundColor: Colors.red,
                ),
              );
            }
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() => _streaming = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('스트림 오류: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final analyzing = context.watch<RecordProvider>().analyzing;

    return Scaffold(
      appBar: AppBar(title: const Text('연주 분석')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _filePicker('연주 음원 (WAV)', _audioFile, true),
            const SizedBox(height: 12),
            _filePicker('악보 파일 (XML)', _sheetFile, false),
            const SizedBox(height: 16),
            _langSelector(),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed:
                  (_audioFile != null && _sheetFile != null && !analyzing && !_streaming)
                      ? _analyze
                      : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.gold,
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8)),
              ),
              child: (analyzing || _streaming)
                  ? Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const SizedBox(
                            height: 16,
                            width: 16,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.black)),
                        const SizedBox(width: 8),
                        Text(analyzing ? '분석 중...' : 'GPT 피드백 생성 중...'),
                      ],
                    )
                  : const Text('분석 시작하기',
                      style: TextStyle(fontWeight: FontWeight.bold)),
            ),
            if (_result != null) ...[
              const SizedBox(height: 24),
              _resultCard(_result!),
            ],
            // SSE 스트리밍: 텍스트 누적 표시
            if (_streaming && _streamText.isNotEmpty) ...[
              const SizedBox(height: 16),
              _streamingCard(),
            ],
            // 스트리밍 완료: 구조화 피드백 카드
            if (_streamedFeedback != null) ...[
              const SizedBox(height: 16),
              FeedbackCard(feedback: _streamedFeedback!),
            ],
          ],
        ),
      ),
    );
  }

  /// GPT 토큰이 도착하는 동안 텍스트를 실시간으로 표시하는 카드
  Widget _streamingCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const SizedBox(
                    height: 14,
                    width: 14,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: AppTheme.gold)),
                const SizedBox(width: 8),
                const Text('GPT 피드백 생성 중...',
                    style: TextStyle(
                        color: AppTheme.gold, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 12),
            Text(_streamText,
                style: Theme.of(context).textTheme.bodyMedium),
          ],
        ),
      ),
    );
  }

  Widget _filePicker(String label, PlatformFile? file, bool isAudio) {
    return InkWell(
      onTap: () => _pickFile(isAudio),
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          border: Border.all(
            color: file != null ? AppTheme.gold : Theme.of(context).dividerColor,
            width: file != null ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Icon(isAudio ? Icons.audio_file : Icons.music_note,
                color: file != null ? AppTheme.gold : null),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                file?.name ?? label,
                style: TextStyle(
                    color: file != null ? AppTheme.gold : null,
                    fontWeight: file != null ? FontWeight.bold : FontWeight.normal),
              ),
            ),
            Icon(Icons.upload_file,
                color: Theme.of(context).textTheme.bodySmall?.color),
          ],
        ),
      ),
    );
  }

  Widget _langSelector() {
    return Row(
      children: _langs.map((l) {
        final selected = _lang == l.$1;
        return Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 3),
            child: OutlinedButton(
              onPressed: () => setState(() => _lang = l.$1),
              style: OutlinedButton.styleFrom(
                backgroundColor:
                    selected ? AppTheme.gold.withOpacity(0.15) : null,
                side: BorderSide(
                    color: selected ? AppTheme.gold : Colors.grey,
                    width: selected ? 2 : 1),
                padding: const EdgeInsets.symmetric(vertical: 10),
              ),
              child: Text(l.$2,
                  style: TextStyle(
                      fontSize: 12,
                      color: selected ? AppTheme.gold : null,
                      fontWeight: selected ? FontWeight.bold : null)),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _resultCard(PracticeRecord r) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('${r.score.toStringAsFixed(1)}점',
                    style: const TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.gold)),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppTheme.gold,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(r.grade,
                      style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.black)),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ScoreBar(
              label: '음정 정확도',
              value: '${r.scoreDetail.correct} / ${r.scoreDetail.total}',
              fraction: r.scoreDetail.total > 0
                  ? r.scoreDetail.correct / r.scoreDetail.total
                  : 0,
            ),
            ScoreBar(
              label: '누락 음표',
              value: '${r.scoreDetail.missedCount}개',
              fraction: r.scoreDetail.total > 0
                  ? 1 - r.scoreDetail.missedCount / r.scoreDetail.total
                  : 1,
              color: Colors.redAccent,
            ),
            ScoreBar(
              label: '박자 오류',
              value: '${r.scoreDetail.wrongTimingCount}개',
              fraction: r.scoreDetail.total > 0
                  ? 1 - r.scoreDetail.wrongTimingCount / r.scoreDetail.total
                  : 1,
              color: Colors.orangeAccent,
            ),
          ],
        ),
      ),
    );
  }
}
