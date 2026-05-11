import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/record.dart';
import '../providers/record_provider.dart';
import '../theme.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<RecordProvider>();
    final records = provider.records;

    return Scaffold(
      appBar: AppBar(title: const Text('피아노 평가')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _statsRow(context, records, provider),
            const SizedBox(height: 24),
            _scoreGraph(context, records),
            const SizedBox(height: 24),
            _recentList(context, records),
          ],
        ),
      ),
    );
  }

  Widget _statsRow(
      BuildContext ctx, List<PracticeRecord> records, RecordProvider p) {
    return Row(
      children: [
        _statCard(ctx, '총 분석', '${records.length}회'),
        const SizedBox(width: 8),
        _statCard(ctx, '평균 점수', '${p.averageScore.toStringAsFixed(1)}점'),
        const SizedBox(width: 8),
        _statCard(ctx, '최고 점수', '${p.highestScore.toStringAsFixed(1)}점'),
      ],
    );
  }

  Widget _statCard(BuildContext ctx, String label, String value) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
          child: Column(
            children: [
              Text(value,
                  style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.gold)),
              const SizedBox(height: 4),
              Text(label,
                  style: Theme.of(ctx).textTheme.bodySmall,
                  textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }

  Widget _scoreGraph(BuildContext ctx, List<PracticeRecord> records) {
    if (records.isEmpty) return const SizedBox.shrink();
    final recent = records.take(10).toList().reversed.toList();
    final maxH = 120.0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('점수 추이',
                style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            SizedBox(
              height: maxH + 24,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: recent.map((r) {
                  final h = (r.score / 100) * maxH;
                  return Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 2),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          Text('${r.score.toStringAsFixed(0)}',
                              style: const TextStyle(
                                  fontSize: 9, color: AppTheme.gold)),
                          const SizedBox(height: 2),
                          Container(
                              height: h,
                              decoration: BoxDecoration(
                                color: AppTheme.gold.withOpacity(0.8),
                                borderRadius: BorderRadius.circular(3),
                              )),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _recentList(BuildContext ctx, List<PracticeRecord> records) {
    if (records.isEmpty) {
      return const Center(
          child: Text('아직 분석 기록이 없습니다.', style: TextStyle(fontSize: 14)));
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('최근 기록',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        ...records.take(5).map((r) => _recordTile(ctx, r)),
      ],
    );
  }

  Widget _recordTile(BuildContext ctx, PracticeRecord r) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(r.title,
            style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text('${r.date} ${r.time}',
            style: Theme.of(ctx).textTheme.bodySmall),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text('${r.score.toStringAsFixed(1)}점',
                style: const TextStyle(
                    color: AppTheme.gold, fontWeight: FontWeight.bold)),
            Text(r.grade, style: Theme.of(ctx).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }
}
