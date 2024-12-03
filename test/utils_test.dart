import 'package:test/test.dart';

import 'package:strike_flutter/utils/stats.dart';

void main() {
  test('Get bells', () {
    var testData = [
      [1, 1],
      [2, 1],
      [3, 1],
      [2, 1]
    ];
    var bells = getBells(testData);

    expect(bells, [1, 2, 3]);
  });

  test('Whole rows', () {
    var bells = [1, 2, 3];
    var testData = [
      [1, 0],
      [2, 0],
      [3, 0],
      [2, 0],
      [1, 0],
      [3, 0]
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
      [1, 0],
      [2, 100],
      [3, 200],
      [1, 300],
      [2, 400],
      [3, 500],
      [1, 700],
      [2, 800],
      [3, 900],
      [1, 1000],
      [2, 1100],
      [3, 1200],
    ];

    var ests = alphaBeta(3, testData, 0.4, 0.1);
    expect(ests, equals(testData));
  });
}
