import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:strike/models/model.dart';

class ScoreWidget extends StatelessWidget {
  const ScoreWidget({super.key});

  @override
  Widget build(context) {
    return Consumer<StrikeModel>(
      builder: (context, strikeModel, child) => Column(
        children: [
          const SizedBox(height: 16),
          Text(
            '(${strikeModel.touchName})',
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: chart(strikeModel.score),
            ),
          ),
        ],
      ),
    );
  }

  Widget chart(double? score) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: FittedBox(
        fit: BoxFit.contain,
        child: Text(score != null ? '${score.round()}%' : ''),
      ),
    );
  }
}
