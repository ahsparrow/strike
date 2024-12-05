import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class StrikeData with ChangeNotifier {
  String host = 'localhost';
  int port = 5000;

  int touchNum = 0;
  List<List<int>> strikeData = [];

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
  Future<List<List<int>>> getTouchData(int touchNum) async {
    final uri =
        Uri(scheme: 'http', host: host, port: port, path: 'log/$touchNum');
    final response = await http.get(uri);

    if (response.statusCode == 200) {
      return [
        for (var x in jsonDecode(response.body) as List) List<int>.from(x)
      ];
    } else {
      return [];
    }
  }
}
