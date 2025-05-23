import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:strike/models/model.dart';

class RmsWidget extends StatelessWidget {
  const RmsWidget({super.key});

  @override
  Widget build(context) {
    var width = MediaQuery.sizeOf(context).width;

    return Consumer<StrikeModel>(
      builder: (context, strikeModel, child) => Column(
        children: [
          const SizedBox(height: 16),
          Text(
            'RMS Accuracy  (${strikeModel.touchName})',
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: chart(width, strikeModel.rms),
            ),
          ),
        ],
      ),
    );
  }

  Widget chart(double width, List<double> rmsData) {
    var barGroups = [
      for (final (n, d) in rmsData.indexed)
        BarChartGroupData(
          x: n + 1,
          barRods: [
            BarChartRodData(
              toY: d * 1000,
              width: width / 2 / rmsData.length,
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
              reservedSize: 40,
            ),
            axisNameSize: 20,
            axisNameWidget: Text('Accuracy (ms)'),
          ),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: AxisTitles(
            sideTitles: SideTitles(showTitles: false),
          ),
        ),
      ),
    );
  }
}
