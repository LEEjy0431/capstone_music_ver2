import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/record_provider.dart';
import '../theme.dart';

class StatsPage extends StatelessWidget {
  const StatsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<RecordProvider>();
    final records = provider.records;

    return Scaffold(
      appBar: AppBar(title: const Text('통계')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                _summaryCard(context, '총 횟수', '${records.length}회'),
                const SizedBox(width: 8),
                _summaryCard(context, '평균 점수',
                    '${provider.averageScore.toStringAsFixed(1)}점'),
                const SizedBox(width: 8),
                _summaryCard(context, '최고 점수',
                    '${provider.highestScore.toStringAsFixed(1)}점'),
              ],
            ),
            const SizedBox(height: 24),
            if (records.isNotEmpty) ...[
              _weekdayChart(context, records
                  .map((r) => r.date)
                  .toList()),
            ] else
              const Center(
                  child: Padding(
                padding: EdgeInsets.all(32),
                child: Text('분석 기록이 없습니다.'),
              )),
          ],
        ),
      ),
    );
  }

  Widget _summaryCard(BuildContext ctx, String label, String value) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
          child: Column(
            children: [
              Text(value,
                  style: const TextStyle(
                      fontSize: 18,
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

  Widget _weekdayChart(BuildContext ctx, List<String> dates) {
    const days = ['월', '화', '수', '목', '금', '토', '일'];
    final counts = List<int>.filled(7, 0);
    for (final d in dates) {
      final dt = DateTime.tryParse(d);
      if (dt != null) {
        counts[(dt.weekday - 1) % 7]++;
      }
    }
    final max = counts.reduce((a, b) => a > b ? a : b);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('요일별 연습 분포',
                style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: List.generate(7, (i) {
                final h = max > 0 ? (counts[i] / max) * 80.0 : 0.0;
                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 3),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        if (counts[i] > 0)
                          Text('${counts[i]}',
                              style: const TextStyle(
                                  fontSize: 10, color: AppTheme.gold)),
                        const SizedBox(height: 2),
                        Container(
                          height: h + 4,
                          decoration: BoxDecoration(
                            color: AppTheme.gold
                                .withOpacity(counts[i] > 0 ? 0.8 : 0.15),
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(days[i],
                            style: Theme.of(ctx).textTheme.bodySmall),
                      ],
                    ),
                  ),
                );
              }),
            ),
          ],
        ),
      ),
    );
  }
}
