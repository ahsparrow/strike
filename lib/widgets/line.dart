import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../data.dart';

class LineWidget extends StatelessWidget {
  const LineWidget({super.key});

  @override
  Widget build(context) {
    return Consumer<StrikeData>(
      builder: (context, strikeData, child) => chart(strikeData.lines),
    );
  }

  Widget chart(List<List<double>> strikeData) {
    return LineChart(
      LineChartData(
        lineBarsData: [
          for (var data in strikeData)
            LineChartBarData(
              spots: [
                for (final (n, x) in data.indexed)
                  FlSpot(n.toDouble(), x.toDouble())
              ],
            )
        ],
      ),
    );
  }
}
