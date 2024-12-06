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
