import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'models/model.dart';
import 'screens/settings.dart';
import 'widgets/line.dart';
import 'widgets/score.dart';
import 'widgets/rms.dart';
import 'widgets/faults.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      create: (context) => StrikeModel(),
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    var settings = context.read<StrikeModel>();
    settings.loadPreferences();

    return MaterialApp(
      title: 'Strike',
      theme: ThemeData.light(),
      darkTheme: ThemeData.dark(),
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

            // Tabs navigator
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
                  icon: Icon(Icons.analytics),
                ),
              ],
            ),

            // Menu actions
            actions: [
              // Settings menu item
              PopupMenuButton(itemBuilder: (context) {
                return [
                  PopupMenuItem<int>(
                    onTap: () async {
                      await Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const Settings(),
                        ),
                      );
                    },
                    child: const Text('Preferences'),
                  ),

                  // Local file menu item
                  PopupMenuItem<int>(
                    onTap: () async {
                      localFiles(context);
                    },
                    child: const Text('Local'),
                  ),

                  // Remote connect menu item
                  PopupMenuItem<int>(
                    onTap: () async {
                      var strikeModel = context.read<StrikeModel>();
                      await strikeModel.remote();
                    },
                    child: const Text('Remote'),
                  ),

                  // About menu item
                  const PopupMenuItem<int>(
                    child: Text('About'),
                  ),
                ];
              })
            ]),

        // Data charts
        body: const TabBarView(children: [
          ScoreWidget(),
          LineWidget(),
          RmsWidget(),
          FaultsWidget(),
        ]),

        // Navigation controls
        bottomNavigationBar: BottomAppBar(
          child: Row(
            children: [
              const Spacer(flex: 1),
              IconButton(
                icon: const Icon(Icons.first_page),
                onPressed: () async {
                  var strikeModel = context.read<StrikeModel>();
                  await strikeModel.getFirst();
                },
              ),
              const SizedBox(width: 24),
              IconButton(
                icon: const Icon(Icons.chevron_left),
                onPressed: () async {
                  var strikeModel = context.read<StrikeModel>();
                  await strikeModel.getPrev();
                },
              ),
              const SizedBox(width: 24),
              IconButton(
                icon: const Icon(Icons.chevron_right),
                onPressed: () async {
                  var strikeModel = context.read<StrikeModel>();
                  await strikeModel.getNext();
                },
              ),
              const SizedBox(width: 24),
              IconButton(
                icon: const Icon(Icons.last_page),
                onPressed: () async {
                  var strikeModel = context.read<StrikeModel>();
                  await strikeModel.getLast();
                },
              ),
              const Spacer(flex: 1),
            ],
          ),
        ),
      ),
    );
  }

  // Get list of local files to analyse
  void localFiles(BuildContext context) async {
    const typeGroup = XTypeGroup(extensions: ['csv']);
    var files = await openFiles(acceptedTypeGroups: [typeGroup]);
    if (files.isEmpty) return;

    var fileNames = [for (var file in files) file.name];
    var data = [for (var file in files) await file.readAsString()];

    if (context.mounted) {
      var strikeModel = context.read<StrikeModel>();
      var errorNames = strikeModel.setLocalData(fileNames, data);

      if (errorNames.isNotEmpty) {
        await showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) {
            return AlertDialog(
              title: const Text('Load touch data'),
              content: Text('Error loading data from ${errorNames.join(", ")}'),
              actions: [
                TextButton(
                  child: const Text('OK'),
                  onPressed: () {
                    Navigator.of(context).pop();
                  },
                )
              ],
            );
          },
        );
      }
    }
  }
}
