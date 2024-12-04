import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
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
          Center(child: Text('Score')),
          Center(child: Text('Line')),
          Center(child: Text('RMS')),
          Center(child: Text('Accuracy')),
        ]),
      ),
    );
  }
}
