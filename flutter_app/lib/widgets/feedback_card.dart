import 'package:flutter/material.dart';

import '../models/record.dart';
import '../theme.dart';

class FeedbackCard extends StatelessWidget {
  final Feedback feedback;

  const FeedbackCard({super.key, required this.feedback});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _section(context, '종합 평가', feedback.overall, Icons.star),
            const Divider(height: 24),
            _section(context, '음정', feedback.pitch, Icons.music_note),
            const SizedBox(height: 12),
            _section(context, '리듬', feedback.rhythm, Icons.av_timer),
            const SizedBox(height: 12),
            _section(context, '타이밍', feedback.timing, Icons.timer),
            if (feedback.tips.isNotEmpty) ...[
              const Divider(height: 24),
              _tipsSection(context),
            ],
            const Divider(height: 24),
            _encouragement(context),
          ],
        ),
      ),
    );
  }

  Widget _section(
      BuildContext ctx, String title, String body, IconData icon) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(children: [
          Icon(icon, size: 16, color: AppTheme.gold),
          const SizedBox(width: 6),
          Text(title,
              style: const TextStyle(
                  fontWeight: FontWeight.bold, color: AppTheme.gold)),
        ]),
        const SizedBox(height: 6),
        Text(body, style: Theme.of(ctx).textTheme.bodyMedium),
      ],
    );
  }

  Widget _tipsSection(BuildContext ctx) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(children: [
          Icon(Icons.lightbulb, size: 16, color: AppTheme.gold),
          SizedBox(width: 6),
          Text('개선 포인트',
              style: TextStyle(
                  fontWeight: FontWeight.bold, color: AppTheme.gold)),
        ]),
        const SizedBox(height: 6),
        ...feedback.tips.map((tip) => Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('• ', style: TextStyle(color: AppTheme.gold)),
                  Expanded(
                      child: Text(tip,
                          style: Theme.of(ctx).textTheme.bodyMedium)),
                ],
              ),
            )),
      ],
    );
  }

  Widget _encouragement(BuildContext ctx) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.gold.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppTheme.gold.withOpacity(0.3)),
      ),
      child: Text(
        feedback.encouragement,
        style: Theme.of(ctx)
            .textTheme
            .bodyMedium
            ?.copyWith(fontStyle: FontStyle.italic),
        textAlign: TextAlign.center,
      ),
    );
  }
}
