import 'package:collection/collection.dart';
import 'package:test/test.dart';

import 'package:strike/utils/stats.dart';

void main() {
  test('Get bells', () {
    var testData = [Strike(1, 1), Strike(2, 1), Strike(3, 1), Strike(2, 1)];
    var bells = getBells(testData);

    expect(bells, [1, 2, 3]);
  });

  test('Whole rows', () {
    var bells = [1, 2, 3];
    var testData = [
      Strike(1, 0),
      Strike(2, 0),
      Strike(3, 0),
      Strike(2, 0),
      Strike(1, 0),
      Strike(3, 0)
    ];

    var strikes = getWholeRows(bells, testData);
    expect(strikes, hasLength(6));

    testData.removeLast();
    strikes = getWholeRows(bells, testData);
    expect(strikes, hasLength(3));

    testData.clear();
    strikes = getWholeRows(bells, testData);
    expect(strikes, hasLength(0));
  });

  test('Alpha Beta', () {
    var testData = [
      Strike(1, 0),
      Strike(2, 100),
      Strike(3, 200),
      Strike(1, 300),
      Strike(2, 400),
      Strike(3, 500),
      Strike(1, 700),
      Strike(2, 800),
      Strike(3, 900),
      Strike(1, 1000),
      Strike(2, 1100),
      Strike(3, 1200),
    ];

    var ests = alphaBeta(3, testData, 0.4, 0.1);

    for (var [t, e] in IterableZip([testData, ests])) {
      expect(t.bell, equals(e.bell));
      expect((t.time - e.time), closeTo(0, 1E-6));
    }
  });
}
