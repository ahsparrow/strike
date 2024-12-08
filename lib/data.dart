import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:collection/collection.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import 'utils/stats.dart';

class StrikeData with ChangeNotifier {
  var host = '192.168.1.102';
  var port = 5000;

  var alpha = 0.4;
  var beta = 0.1;

  int touchNum = 0;
  List<Strike> strikeData = [];

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

      notifyListeners();
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
  }
}
