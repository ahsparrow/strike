import 'package:collection/collection.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:strike/models/model.dart';

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
    var width = MediaQuery.sizeOf(context).width;
    var nRows = width ~/ 30;

    return Consumer<StrikeModel>(
      builder: (context, strikeData, child) => Column(
        children: [
          const SizedBox(height: 16),
          Text(
            '(${strikeData.touchName})',
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: chart(
                  strikeData.lines,
                  strikeData.showEstimates ? strikeData.ests : [],
                  sliderValue,
                  nRows),
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

  Widget chart(List<List<double>> strikeData, List<List<double>> estData,
      double start, int nRows) {
    // Calculate display indices
    var startIdx = 0;
    var stopIdx = 0;
    if (strikeData.isNotEmpty) {
      final len = strikeData[0].length;
      if (len > nRows) {
        startIdx = (start * (len - nRows)).round();
        stopIdx = startIdx + nRows;
      } else {
        stopIdx = len;
      }
    }

    return LineChart(
      duration: Duration.zero,
      LineChartData(
        lineBarsData: [
              for (var (bell, data) in strikeData.indexed)
                LineChartBarData(
                  spots: spots(data, startIdx, stopIdx),
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
                  spots: spots(data, startIdx, stopIdx),
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
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              interval: 2,
              reservedSize: 30,
            ),
          ),
          leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
      ),
    );
  }

  List<FlSpot> spots(List<double> data, int start, int stop) {
    if (data.isEmpty) {
      return [];
    } else {
      return [
        for (final (n, x) in data.slice(start, stop).indexed)
          FlSpot((n + start).toDouble() + 1, x.toDouble())
      ];
    }
  }
}
