import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'data.dart';
import 'widgets/line.dart';
import 'widgets/score.dart';
import 'widgets/rms.dart';
import 'widgets/accuracy.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      create: (context) => StrikeData(),
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Strike',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        brightness: Brightness.dark,
      ),
      themeMode: ThemeMode.system,
      home: const MyHomePage(title: 'Strike'),
    );
  }
}

class MyHomePage extends StatelessWidget {
  const MyHomePage({super.key, required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      initialIndex: 0,
      length: 4,
      child: Scaffold(
        appBar: AppBar(
          backgroundColor: Theme.of(context).colorScheme.inversePrimary,
          title: Text(title),
          bottom: const TabBar(
            tabs: [
              Tab(
                icon: Icon(Icons.percent),
              ),
              Tab(
                icon: Icon(Icons.show_chart),
              ),
              Tab(
                icon: Icon(Icons.bar_chart),
              ),
              Tab(
                icon: Icon(Icons.donut_large),
              ),
            ],
          ),
        ),
        body: const TabBarView(children: [
          ScoreWidget(),
          LineWidget(),
          RmsWidget(),
          AccuracyWidget(),
        ]),
        bottomNavigationBar: BottomAppBar(
          child: Row(
            children: [
              const Spacer(flex: 1),
              IconButton(
                icon: const Icon(Icons.first_page),
                onPressed: () {},
              ),
              const SizedBox(width: 24),
              IconButton(
                icon: const Icon(Icons.chevron_left),
                onPressed: () async {
                  var strikeData = context.read<StrikeData>();
                  strikeData.decrement();
                },
              ),
              const SizedBox(width: 24),
              IconButton(
                icon: const Icon(Icons.chevron_right),
                onPressed: () async {
                  var strikeData = context.read<StrikeData>();
                  strikeData.increment();
                },
              ),
              const SizedBox(width: 24),
              IconButton(
                icon: const Icon(Icons.last_page),
                onPressed: () {},
              ),
              const Spacer(flex: 1),
            ],
          ),
        ),
      ),
    );
  }
}
