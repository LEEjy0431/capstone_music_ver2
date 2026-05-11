import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/record.dart';
import '../providers/record_provider.dart';
import '../theme.dart';

class HistoryPage extends StatefulWidget {
  const HistoryPage({super.key});

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final records = context.watch<RecordProvider>().records;
    final filtered = records
        .where((r) => r.title.toLowerCase().contains(_query.toLowerCase()))
        .toList();

    return Scaffold(
      appBar: AppBar(title: const Text('연습 기록')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              onChanged: (v) => setState(() => _query = v),
              decoration: InputDecoration(
                hintText: '곡 이름 검색...',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8)),
                contentPadding: const EdgeInsets.symmetric(vertical: 0),
              ),
            ),
          ),
          Expanded(
            child: filtered.isEmpty
                ? const Center(child: Text('기록이 없습니다.'))
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: filtered.length,
                    itemBuilder: (_, i) => _tile(context, filtered[i]),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _tile(BuildContext ctx, PracticeRecord r) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: AppTheme.gold.withOpacity(0.15),
          child: Text(r.grade,
              style: const TextStyle(
                  color: AppTheme.gold, fontWeight: FontWeight.bold)),
        ),
        title: Text(r.title,
            style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle:
            Text('${r.date} ${r.time}', style: Theme.of(ctx).textTheme.bodySmall),
        trailing: Text('${r.score.toStringAsFixed(1)}점',
            style: const TextStyle(
                color: AppTheme.gold, fontWeight: FontWeight.bold)),
      ),
    );
  }
}
