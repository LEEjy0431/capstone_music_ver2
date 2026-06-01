import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/record_provider.dart';
import '../theme.dart';

class ProfilePage extends StatefulWidget {
  final bool darkMode;
  final ValueChanged<bool> onDarkModeChanged;

  const ProfilePage({
    super.key,
    required this.darkMode,
    required this.onDarkModeChanged,
  });

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  String _name = '피아니스트';
  String _goal = '매일 30분 연습';

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<RecordProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('프로필')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _avatar(),
            const SizedBox(height: 16),
            _infoCard(context),
            const SizedBox(height: 16),
            _settingsCard(context),
            const SizedBox(height: 16),
            _badgesCard(context, provider.records.length,
                provider.highestScore),
          ],
        ),
      ),
    );
  }

  Widget _avatar() {
    return CircleAvatar(
      radius: 48,
      backgroundColor: AppTheme.gold.withOpacity(0.2),
      child: const Icon(Icons.person, size: 56, color: AppTheme.gold),
    );
  }

  Widget _infoCard(BuildContext ctx) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _editField(ctx, '이름', _name, (v) => setState(() => _name = v)),
            const Divider(height: 24),
            _editField(ctx, '목표', _goal, (v) => setState(() => _goal = v)),
          ],
        ),
      ),
    );
  }

  Widget _editField(
      BuildContext ctx, String label, String value, ValueChanged<String> onSaved) {
    return Row(
      children: [
        SizedBox(
            width: 48,
            child: Text(label, style: Theme.of(ctx).textTheme.bodySmall)),
        const SizedBox(width: 12),
        Expanded(
          child: TextFormField(
            initialValue: value,
            style: const TextStyle(fontWeight: FontWeight.bold),
            onChanged: onSaved,
            decoration: const InputDecoration(
              border: InputBorder.none,
              isDense: true,
            ),
          ),
        ),
        const Icon(Icons.edit, size: 16, color: AppTheme.gold),
      ],
    );
  }

  Widget _settingsCard(BuildContext ctx) {
    return Card(
      child: SwitchListTile(
        title: const Text('다크 모드'),
        value: widget.darkMode,
        onChanged: widget.onDarkModeChanged,
        activeColor: AppTheme.gold,
      ),
    );
  }

  Widget _badgesCard(BuildContext ctx, int count, double highest) {
    final badges = <(String, String, bool)>[
      ('첫 분석', '첫 번째 연주 분석 완료', count >= 1),
      ('10회 달성', '10회 분석 완료', count >= 10),
      ('80점 달성', '80점 이상 획득', highest >= 80),
      ('90점 달성', '90점 이상 획득', highest >= 90),
    ];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('뱃지',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: badges.map((b) => _badge(ctx, b.$1, b.$2, b.$3)).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _badge(BuildContext ctx, String title, String desc, bool earned) {
    return Tooltip(
      message: desc,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: earned ? AppTheme.gold.withOpacity(0.15) : null,
          border: Border.all(
              color: earned ? AppTheme.gold : Colors.grey.withOpacity(0.3)),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          title,
          style: TextStyle(
              fontSize: 12,
              color: earned ? AppTheme.gold : Colors.grey,
              fontWeight: earned ? FontWeight.bold : FontWeight.normal),
        ),
      ),
    );
  }
}
