import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/record.dart';
import '../providers/record_provider.dart';
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

    final record = await provider.analyze(
      sheetBytes: _sheetFile!.bytes!,
      sheetName: _sheetFile!.name,
      audioBytes: _audioFile!.bytes!,
      audioName: _audioFile!.name,
      title: _sheetFile!.name.replaceAll(RegExp(r'\.\w+$'), ''),
      lang: _lang,
    );

    if (record != null) {
      setState(() => _result = record);
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(provider.error ?? '분석 실패'),
          backgroundColor: Colors.red,
        ),
      );
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
              onPressed: (_audioFile != null && _sheetFile != null && !analyzing)
                  ? _analyze
                  : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.gold,
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8)),
              ),
              child: analyzing
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.black))
                  : const Text('분석 시작하기',
                      style: TextStyle(fontWeight: FontWeight.bold)),
            ),
            if (_result != null) ...[
              const SizedBox(height: 24),
              _resultCard(_result!),
              const SizedBox(height: 16),
              FeedbackCard(feedback: _result!.feedback),
            ],
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
            color: file != null
                ? AppTheme.gold
                : Theme.of(context).dividerColor,
            width: file != null ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Icon(
              isAudio ? Icons.audio_file : Icons.music_note,
              color: file != null ? AppTheme.gold : null,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                file?.name ?? label,
                style: TextStyle(
                    color: file != null ? AppTheme.gold : null,
                    fontWeight:
                        file != null ? FontWeight.bold : FontWeight.normal),
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
              value:
                  '${r.scoreDetail.correct} / ${r.scoreDetail.total}',
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
                  ? 1 -
                      r.scoreDetail.wrongTimingCount / r.scoreDetail.total
                  : 1,
              color: Colors.orangeAccent,
            ),
          ],
        ),
      ),
    );
  }
}
