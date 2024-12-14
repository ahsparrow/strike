import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:collection/collection.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'package:strike_flutter/utils/stats.dart' as stats;

class StrikeModel with ChangeNotifier {
  // CANBell server connection
  var host = '192.168.4.1';
  var port = 80;

  // Alpha/beta filter parameters
  var alpha = 0.4;
  var beta = 0.1;

  // Striking error threshold
  int thresholdMs = 50;

  // Show estimates on line plot
  bool showEstimates = false;

  // Include rounds at start and end of touch
  bool includeRounds = true;

  // Strike data
  int touchNum = 0;
  List<stats.Strike> strikeData = [];
  List<List<stats.Strike>> localStrikeData = [];

  // Calculation results
  List<List<double>> lines = [];
  List<List<double>> ests = [];
  double? score;
  List<double> rms = [];
  List<Map<String, Map<String, double>>> faults = [];

  Future<void> getFirst() async {
    final numTouches = await getNumTouches();
    if (numTouches > 0) {
      await getTouch(1);
    }
  }

  Future<void> getLast() async {
    final numTouches = await getNumTouches();
    if (numTouches > 0) {
      await getTouch(numTouches);
    }
  }

  Future<void> getNext() async {
    final numTouches = await getNumTouches();
    if (numTouches > 0) {
      final n = min(numTouches, touchNum + 1);
      await getTouch(n);
    }
  }

  Future<void> getPrev() async {
    final numTouches = await getNumTouches();
    if (numTouches > 0) {
      final n = max(1, touchNum - 1);
      await getTouch(n);
    }
  }

  Future<void> getTouch(int num) async {
    strikeData = await getTouchData(num);
    if (strikeData.isNotEmpty) {
      touchNum = num;

      calculate();
    }
  }

  // Query number of touches stored on the server
  Future<int> getNumTouches() async {
    if (localStrikeData.isNotEmpty) {
      return localStrikeData.length;
    } else {
      final uri = Uri(scheme: 'http', host: host, port: port, path: '/log/');
      final response = await http.get(uri);

      return jsonDecode(response.body) as int;
    }
  }

  // Get touch data from the server
  Future<List<stats.Strike>> getTouchData(int touchNum) async {
    if (localStrikeData.isNotEmpty) {
      return localStrikeData[touchNum - 1];
    } else {
      final uri =
          Uri(scheme: 'http', host: host, port: port, path: 'log/$touchNum');
      final response = await http.get(uri);

      if (response.statusCode == 200) {
        return [
          for (var x in jsonDecode(response.body) as List)
            stats.Strike(x[0], x[1].toDouble() / 1000)
        ];
      } else {
        return [];
      }
    }
  }

  // Switch to remote mode
  Future<void> remote() async {
    localStrikeData = [];
    strikeData = [];

    await getLast();
  }

  // Parse and store local touch data
  List<String> setLocalData(List<String> fileNames, List<String> data) {
    List<List<stats.Strike>> strikeData = [];
    List<String> badNames = [];

    for (var [name, touch] in IterableZip([fileNames, data])) {
      try {
        var strikes = [
          for (var [bell, time] in jsonDecode(touch))
            stats.Strike(bell, time.toDouble() / 1000)
        ];
        strikeData.add(strikes);
      } on FormatException {
        debugPrint('Invalid JSON format');
        badNames.add(name);
      } on TypeError {
        debugPrint("Can't decode strike data");
        badNames.add(name);
      }
    }
    localStrikeData = strikeData;

    // Update results
    getTouch(0);

    return badNames;
  }

  // Calculate resutls
  void calculate() {
    if (strikeData.isEmpty) {
      this.lines = [];
      this.ests = [];
      score = null;
      rms = [];

      return;
    }

    // Striking data
    final bells = stats.getBells(strikeData);
    final nbells = bells.length;
    var strikes = stats.getWholeRows(bells, strikeData);
    var rows = strikes.slices(bells.length).toList();

    if (!includeRounds) {
      // Remove rounds from start and end
      final startStop = stats.methodStartStop(rows);
      if (startStop != null) {
        final (first, last) = startStop;
        rows = rows.sublist(first, last);
        strikes = strikes.sublist(first * nbells, last * nbells);
      }
    }

    // Calculate estimates
    final estStrikes = stats.alphaBeta(nbells, strikes, alpha, beta);

    // Split data into rows
    final sortedRows = [
      for (final r in rows) r.sorted((a, b) => a.bell.compareTo(b.bell))
    ];

    final estRows = estStrikes.slices(nbells);
    final sortedEstRows = [
      for (final r in estRows) r.sorted((a, b) => a.bell.compareTo(b.bell))
    ];

    // Reference times for the line plot
    final refs = [for (final r in estRows) r[0].time];

    // Calculate line plot offsets
    List<List<double>> lines = [];
    List<List<double>> ests = [];
    for (var n = 0; n < nbells; n++) {
      var times = [for (final x in sortedRows) x[n].time];
      var line = [
        for (final [time, ref] in IterableZip([times, refs])) time - ref
      ];
      lines.add(line);

      times = [for (final x in sortedEstRows) x[n].time];
      var est = [
        for (final [time, ref] in IterableZip([times, refs])) time - ref
      ];
      ests.add(est);
    }

    this.lines = lines;
    this.ests = ests;

    score = stats.score(nbells, strikes, estStrikes, thresholdMs / 1000);

    rms = stats.rms(nbells, sortedRows, sortedEstRows);

    faults =
        stats.faults(nbells, sortedRows, sortedEstRows, thresholdMs / 1000);

    notifyListeners();
  }

  // Save settings to shared preferences
  void savePreferences() async {
    final SharedPreferencesAsync prefs = SharedPreferencesAsync();

    await prefs.setString('host', host);
    await prefs.setInt('port', port);
    await prefs.setInt('threshold', thresholdMs);
    await prefs.setDouble('alpha', alpha);
    await prefs.setDouble('beta', beta);
    await prefs.setBool('estimates', showEstimates);
    await prefs.setBool('rounds', includeRounds);
  }

  // Load settings from shared preferences
  void loadPreferences() async {
    final SharedPreferencesAsync prefs = SharedPreferencesAsync();

    host = await prefs.getString('host') ?? '192.168.4.1';
    port = await prefs.getInt('port') ?? 80;

    thresholdMs = await prefs.getInt('threshold') ?? 50;

    alpha = await prefs.getDouble('alpha') ?? 0.4;
    beta = await prefs.getDouble('beta') ?? 0.1;

    showEstimates = await prefs.getBool('estimates') ?? false;

    includeRounds = await prefs.getBool('rounds') ?? true;
  }

  void setPreferences(
      {required String host,
      required int port,
      required int thresholdMs,
      required double alpha,
      required double beta,
      required bool showEstimates,
      required bool includeRounds}) {
    this.host = host;
    this.port = port;
    this.thresholdMs = thresholdMs;
    this.alpha = alpha;
    this.beta = beta;
    this.showEstimates = showEstimates;
    this.includeRounds = includeRounds;

    calculate();
  }
}
