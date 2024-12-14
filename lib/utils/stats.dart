import 'dart:math';
import 'package:collection/collection.dart';

class Strike {
  int bell;
  double time;

  Strike(this.bell, this.time);
}

// Returns a sorted list of bells from the strike data
List<int> getBells(List<Strike> strikes) {
  var bells = strikes.map((x) => x.bell).toSet().toList();
  bells.sort();

  return bells;
}

// Remove incomplete rows from end of strikes
List<Strike> getWholeRows(List<int> bells, List<Strike> strikes) {
  var rows = strikes.slices(bells.length);

  var lastRow = 0;
  for (final row in rows) {
    if (row.map((x) => x.bell).toSet().length == bells.length) {
      lastRow += 1;
    } else {
      break;
    }
  }
  return strikes.sublist(0, lastRow * bells.length);
}

// Find start and stop of method
(int, int)? methodStartStop(List<List<Strike>> rows) {
  var first = 0;
  var last = rows.length - 1;
  final rounds = [for (var i = 0; i < rows[0].length; i++) i + 1];

  // Search from start
  for (var (n, row) in rows.indexed) {
    var bells = row.map((x) => x.bell);
    if (!const IterableEquality().equals(bells, rounds)) {
      first = n;
      break;
    }
  }

  // Search from end
  for (var (n, row) in rows.reversed.indexed) {
    if (!const IterableEquality().equals(row, rounds)) {
      last = rows.length - n - 1;
      break;
    }
  }

  // Nothing but rounds
  if (last == 0) {
    return null;
  }

  // Add one or two rows of rounds before start
  if (first != 0) {
    first = ((first - 1) ~/ 2) * 2;
  }

  // Add a row of rounds after finish
  if (last != rows.length - 1) {
    last += 1;
  }

  return (first, last);
}

// Alpha Beta filter (see https://en.wikipedia.org/wiki/Alpha_beta_filter)
List<Strike> alphaBeta(
    int nbells, List<Strike> strikes, double alpha, double beta) {
  var times = strikes.map((x) => x.time).toList();

  var tk_1 = times[0].toDouble();
  var dk_1 =
      (times.last - tk_1) / (times.length + times.length / (2 * nbells) - 2);

  var ests = [Strike(strikes[0].bell, tk_1)];

  for (final (n, time) in times.slice(1).indexed) {
    var gap = ((n + 1) % (nbells * 2) == 0) ? 2 : 1;

    var tk = tk_1 + dk_1 * gap;
    var rk = time - tk;

    tk_1 = tk + alpha * rk;
    dk_1 += beta * rk;

    ests.add(Strike(strikes[n + 1].bell, tk_1));
  }

  return ests;
}

// Overall percentage score for a touch
double score(
    int nbells, List<Strike> strikes, List<Strike> ests, double threshold) {
  var errs = [
    for (var p in IterableZip([strikes, ests])) p[0].time - p[1].time
  ];

  var rows = errs.slices(nbells);
  var goodRows = rows.where((row) => row.max < threshold).length;

  return goodRows / rows.length * 100;
}

List<double> rms(
    int nbells, List<List<Strike>> sortedRows, List<List<Strike>> sortedEsts) {
  List<double> out = [];
  for (var bell = 0; bell < nbells; bell++) {
    var errs = [
      for (var [row, est] in IterableZip([sortedRows, sortedEsts]))
        row[bell].time - est[bell].time
    ];
    out.add(sqrt([for (var e in errs) e * e].average));
  }

  return out;
}

List<Map<String, Map<String, double>>> faults(
    int nbells,
    List<List<Strike>> sortedRows,
    List<List<Strike>> sortedEsts,
    double threshold) {
  List<Map<String, Map<String, double>>> out = [];

  for (var bell = 0; bell < nbells; bell++) {
    var errs = [
      for (var [row, est] in IterableZip([sortedRows, sortedEsts]))
        row[bell].time - est[bell].time
    ];

    var hand = [for (var i = 0; i < errs.length; i += 2) errs[i]];
    var back = [for (var i = 1; i < errs.length; i += 2) errs[i]];

    var handEarly = hand.where((x) => x < -threshold).length / hand.length;
    var handLate = hand.where((x) => x > threshold).length / hand.length;
    var backEarly = back.where((x) => x < -threshold).length / back.length;
    var backLate = back.where((x) => x > threshold).length / back.length;

    out.add({
      'hand': {'early': handEarly, 'late': handLate},
      'back': {'early': backEarly, 'late': backLate},
    });
  }

  return out;
}
