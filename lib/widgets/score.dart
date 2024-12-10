import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:strike_flutter/models/model.dart';

class ScoreWidget extends StatelessWidget {
  const ScoreWidget({super.key});

  @override
  Widget build(context) {
    return Consumer<StrikeModel>(
      builder: (context, strikeData, child) => chart(strikeData.score ?? 0),
    );
  }

  Widget chart(double score) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: FittedBox(
        fit: BoxFit.contain,
        child: Text('${score.round()}%'),
      ),
    );
  }
}
