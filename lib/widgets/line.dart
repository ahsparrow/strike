import 'package:collection/collection.dart';
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

class LineWidget extends StatefulWidget {
  const LineWidget({super.key});

  @override
  State<LineWidget> createState() => LineWidgetState();
}

class LineWidgetState extends State<LineWidget> {
  double sliderValue = 0;

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
              child: chart(strikeData.lines,
                  strikeData.showEstimates ? strikeData.ests : [], sliderValue),
            ),
          ),
          Slider(
            value: sliderValue,
            max: 1.0,
            divisions: null,
            onChanged: (double value) {
              setState(() {
                sliderValue = value;
              });
            },
          ),
        ],
      ),
    );
  }

  Widget chart(
      List<List<double>> strikeData, List<List<double>> estData, double start) {
    // Calculate display indices
    final len = strikeData[0].length;
    var i1 = 0;
    var i2 = len;
    if (len > 24) {
      i1 = (start * (strikeData[0].length - 24)).round();
      i2 = i1 + 24;
    }

    return LineChart(
      LineChartData(
        lineBarsData: [
              for (var (bell, data) in strikeData.indexed)
                LineChartBarData(
                  spots: [
                    for (final (n, x) in data.slice(i1, i2).indexed)
                      FlSpot(n.toDouble() + i1, x.toDouble())
                  ],
                  dotData: FlDotData(
                    show: true,
                    getDotPainter: (spot, percent, barDatat, index) {
                      return FlDotCirclePainter(
                        radius: 4,
                        color: lineColors[bell],
                      );
                    },
                  ),
                  color: lineColors[bell],
                )
            ] +
            [
              for (var (bell, data) in estData.indexed)
                LineChartBarData(
                  spots: [
                    for (final (n, x) in data.slice(i1, i2).indexed)
                      FlSpot(n.toDouble() + i1, x.toDouble())
                  ],
                  dotData: FlDotData(
                    show: true,
                    getDotPainter: (spot, percent, barDatat, index) {
                      return FlDotCrossPainter(
                        color: lineColors[bell],
                      );
                    },
                  ),
                  color: lineColors[bell],
                  barWidth: 0,
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
