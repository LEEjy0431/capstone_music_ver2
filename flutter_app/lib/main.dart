import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'providers/record_provider.dart';
import 'theme.dart';
import 'pages/home_page.dart';
import 'pages/analysis_page.dart';
import 'pages/history_page.dart';
import 'pages/stats_page.dart';
import 'pages/profile_page.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      create: (_) => RecordProvider(),
      child: const PianoEvalApp(),
    ),
  );
}

class PianoEvalApp extends StatefulWidget {
  const PianoEvalApp({super.key});

  @override
  State<PianoEvalApp> createState() => _PianoEvalAppState();
}

class _PianoEvalAppState extends State<PianoEvalApp> {
  bool _dark = true;
  int _tab = 0;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '피아노 평가',
      debugShowCheckedModeBanner: false,
      theme: _dark ? AppTheme.dark() : AppTheme.light(),
      home: _Shell(
        tab: _tab,
        dark: _dark,
        onTabChanged: (i) => setState(() => _tab = i),
        onDarkChanged: (v) => setState(() => _dark = v),
      ),
    );
  }
}

class _Shell extends StatelessWidget {
  final int tab;
  final bool dark;
  final ValueChanged<int> onTabChanged;
  final ValueChanged<bool> onDarkChanged;

  const _Shell({
    required this.tab,
    required this.dark,
    required this.onTabChanged,
    required this.onDarkChanged,
  });

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      const HomePage(),
      const AnalysisPage(),
      const HistoryPage(),
      const StatsPage(),
      ProfilePage(darkMode: dark, onDarkModeChanged: onDarkChanged),
    ];

    return Scaffold(
      body: pages[tab],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: tab,
        onTap: onTabChanged,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: '홈'),
          BottomNavigationBarItem(icon: Icon(Icons.mic), label: '분석'),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: '기록'),
          BottomNavigationBarItem(icon: Icon(Icons.bar_chart), label: '통계'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: '프로필'),
        ],
      ),
    );
  }
}
