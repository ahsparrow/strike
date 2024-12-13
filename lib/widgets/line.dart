import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:strike_flutter/models/model.dart';

const lineColors = [
  Colors.grey,
  Colors.red,
  Colors.orange,
  Colors.yellow,
  Colors.green,
  Colors.blue,
  Colors.teal,
  Colors.cyan,
];

class LineWidget extends StatelessWidget {
  const LineWidget({super.key});

  @override
  Widget build(context) {
    return Consumer<StrikeModel>(
      builder: (context, strikeData, child) => Column(
        children: [
          const SizedBox(height: 16),
          Text(
            'Touch ${strikeData.touchNum}',
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: chart(strikeData.lines),
            ),
          ),
        ],
      ),
    );
  }

  Widget chart(List<List<double>> strikeData) {
    return LineChart(
      LineChartData(
        lineBarsData: [
          for (var (line, data) in strikeData.indexed)
            LineChartBarData(
              spots: [
                for (final (n, x) in data.indexed)
                  FlSpot(n.toDouble(), x.toDouble())
              ],
              dotData: FlDotData(
                show: true,
                getDotPainter: (spot, percent, barDatat, index) {
                  return FlDotCirclePainter(
                    radius: 4,
                    color: lineColors[line],
                  );
                },
              ),
              color: lineColors[line],
            )
        ],
        borderData: FlBorderData(show: false),
        gridData: const FlGridData(show: false),
        lineTouchData: const LineTouchData(enabled: false),
        titlesData: const FlTitlesData(
            leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
            rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
            topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false))),
      ),
    );
  }
}
