import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:collection/collection.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'package:strike_flutter/utils/stats.dart';

class StrikeModel with ChangeNotifier {
  // CANBell server connection
  var host = '192.168.1.102';
  var port = 5000;

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
  List<Strike> strikeData = [];

  // Calculation results
  List<List<double>> lines = [];
  List<List<double>> ests = [];

  void getFirst() async {
    final numTouches = await getNumTouches();
    if (numTouches > 0) {
      getTouch(1);
    }
  }

  void getLast() async {
    final numTouches = await getNumTouches();
    if (numTouches > 0) {
      getTouch(numTouches);
    }
  }

  void getNext() async {
    final numTouches = await getNumTouches();
    if (numTouches > 0) {
      final n = min(numTouches, touchNum + 1);
      getTouch(n);
    }
  }

  void getPrev() async {
    final numTouches = await getNumTouches();
    if (numTouches > 0) {
      final n = max(1, touchNum - 1);
      getTouch(n);
    }
  }

  void getTouch(int num) async {
    strikeData = await getTouchData(num);
    if (strikeData.isNotEmpty) {
      touchNum = num;

      calculate();
    }
  }

  // Query number of touches stored on the server
  Future<int> getNumTouches() async {
    final uri = Uri(scheme: 'http', host: host, port: port, path: '/log/');
    final response = await http.get(uri);

    return jsonDecode(response.body) as int;
  }

  // Get touch data from the server
  Future<List<Strike>> getTouchData(int touchNum) async {
    final uri =
        Uri(scheme: 'http', host: host, port: port, path: 'log/$touchNum');
    final response = await http.get(uri);

    if (response.statusCode == 200) {
      return [
        for (var x in jsonDecode(response.body) as List)
          Strike(x[0], x[1].toDouble() / 1000)
      ];
    } else {
      return [];
    }
  }

  // Calculate resutls
  calculate() {
    if (strikeData.isEmpty) {
      return;
    }

    final bells = getBells(strikeData);
    final strikes = getWholeRows(bells, strikeData);
    final estStrikes = alphaBeta(bells.length, strikes, alpha, beta);

    final rows = strikes.slices(bells.length);
    final sortedRows = [
      for (final r in rows) r.sorted((a, b) => a.bell.compareTo(b.bell))
    ];

    final estRows = estStrikes.slices(bells.length);
    final sortedEstRows = [
      for (final r in estRows) r.sorted((a, b) => a.bell.compareTo(b.bell))
    ];

    final refs = [for (final r in estRows) r[0].time];

    List<List<double>> lines = [];
    List<List<double>> ests = [];
    for (var n = 0; n < bells.length; n++) {
      var times = [for (final x in sortedRows) x[n].time];
      var line = [
        for (final pair in IterableZip([times, refs])) pair[0] - pair[1]
      ];
      lines.add(line);

      times = [for (final x in sortedEstRows) x[n].time];
      var est = [
        for (final pair in IterableZip([times, refs])) pair[0] - pair[1]
      ];
      ests.add(est);
    }

    this.lines = lines;
    this.ests = ests;

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

    thresholdMs = await prefs.getInt('thresholdMs') ?? 50;

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
