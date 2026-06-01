import 'package:flutter/material.dart';

import '../theme.dart';

class ScoreBar extends StatelessWidget {
  final String label;
  final String value;
  final double fraction; // 0.0 ~ 1.0
  final Color? color;

  const ScoreBar({
    super.key,
    required this.label,
    required this.value,
    required this.fraction,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final barColor = color ?? AppTheme.gold;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: Theme.of(context).textTheme.bodySmall),
              Text(value,
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: fraction.clamp(0.0, 1.0),
              minHeight: 8,
              backgroundColor: barColor.withOpacity(0.15),
              valueColor: AlwaysStoppedAnimation<Color>(barColor),
            ),
          ),
        ],
      ),
    );
  }
}
