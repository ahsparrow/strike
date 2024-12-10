import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:strike_flutter/models/model.dart';

class RmsWidget extends StatelessWidget {
  const RmsWidget({super.key});

  @override
  Widget build(context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Consumer<StrikeModel>(
        builder: (context, strikeData, child) => chart(strikeData.rms),
      ),
    );
  }

  Widget chart(List<double> rmsData) {
    var barGroups = [
      for (final (n, d) in rmsData.indexed)
        BarChartGroupData(
          x: n + 1,
          barRods: [
            BarChartRodData(
              toY: d * 1000,
              width: 64,
              borderRadius: const BorderRadius.all(Radius.circular(0)),
            ),
          ],
        )
    ];

    return BarChart(
      BarChartData(
        barGroups: barGroups,
        barTouchData: BarTouchData(enabled: false),
        maxY: 100,
        borderData: FlBorderData(show: true),
        gridData: const FlGridData(show: false),
        titlesData: const FlTitlesData(
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              interval: 10,
              reservedSize: 60,
            ),
          ),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
      ),
    );
  }
}
