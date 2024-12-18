import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:strike/models/model.dart';

class FaultsWidget extends StatelessWidget {
  const FaultsWidget({super.key});

  @override
  Widget build(context) {
    var width = MediaQuery.sizeOf(context).width;

    return Consumer<StrikeModel>(
      builder: (context, strikeData, child) => Column(
        children: [
          const SizedBox(height: 16),
          Text(
            'Early/Late, ${strikeData.thresholdMs}ms threshold  (Touch ${strikeData.touchNum})',
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: chart(width, strikeData.faults),
            ),
          ),
        ],
      ),
    );
  }

  Widget chart(double width, List<Map<String, Map<String, double>>> faults) {
    var barGroups = [
      for (final (n, fault) in faults.indexed)
        BarChartGroupData(
          x: n + 1,
          barRods: [
            BarChartRodData(
              toY: fault['hand']!['late']! * 100,
              fromY: -fault['hand']!['early']! * 100,
              width: width / 4 / faults.length,
              borderRadius: const BorderRadius.all(Radius.circular(0)),
              color: Colors.transparent,
              rodStackItems: [
                BarChartRodStackItem(
                  0,
                  fault['hand']!['late']! * 100,
                  Colors.teal,
                ),
                BarChartRodStackItem(
                  -fault['hand']!['early']! * 100,
                  0,
                  Colors.red,
                )
              ],
            ),
            BarChartRodData(
              toY: fault['back']!['late']! * 100,
              fromY: -fault['back']!['early']! * 100,
              width: width / 4 / faults.length,
              borderRadius: const BorderRadius.all(Radius.circular(0)),
              color: Colors.transparent,
              rodStackItems: [
                BarChartRodStackItem(
                  0,
                  fault['back']!['late']! * 100,
                  Colors.indigo,
                ),
                BarChartRodStackItem(
                  -fault['back']!['early']! * 100,
                  0,
                  Colors.amber,
                )
              ],
            ),
          ],
        )
    ];

    return BarChart(
      BarChartData(
        barGroups: barGroups,
        barTouchData: BarTouchData(enabled: false),
        maxY: 60,
        minY: -60,
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
            axisNameWidget: Text('Percentage blows early/late'),
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
