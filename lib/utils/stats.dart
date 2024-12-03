import 'package:collection/collection.dart';

// Returns a sorted list of bells from the strike data
List<int> getBells(List<List<int>> strikes) {
  var bells = strikes.map((x) => x[0]).toSet().toList();
  bells.sort();

  return bells;
}

// Remove incomplete rows from end of strikes
List<List<int>> getWholeRows(List<int> bells, List<List<int>> strikes) {
  var rows = strikes.slices(bells.length);

  var lastRow = 0;
  for (final row in rows) {
    if (row.map((x) => x[0]).toSet().length == bells.length) {
      lastRow += 1;
    } else {
      break;
    }
  }
  return strikes.sublist(0, lastRow * bells.length);
}

// Alpha Beta filter (see https://en.wikipedia.org/wiki/Alpha_beta_filter)
List<List<int>> alphaBeta(
    int nbells, List<List<int>> strikes, double alpha, double beta) {
  var times = strikes.map((x) => x[1]).toList();

  var tk_1 = times[0].toDouble();
  var dk_1 =
      (times.last - tk_1) / (times.length + times.length / (2 * nbells) - 2);

  var ests = [
    [strikes[0][0], tk_1.round()]
  ];

  for (final (n, time) in times.slice(1).indexed) {
    var gap = ((n + 1) % (nbells * 2) == 0) ? 2 : 1;

    var tk = tk_1 + dk_1 * gap;
    var rk = time - tk;

    tk_1 = tk + alpha * rk;
    dk_1 += beta * rk;

    ests.add([strikes[n + 1][0], tk_1.round()]);
  }

  return ests;
}
