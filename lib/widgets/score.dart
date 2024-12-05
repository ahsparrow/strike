import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../data.dart';

class ScoreWidget extends StatelessWidget {
  const ScoreWidget({super.key});

  @override
  Widget build(context) {
    return Center(
      child: Consumer<StrikeData>(
        builder: (context, strikeData, child) => Text(
          '${strikeData.touchNum}',
        ),
      ),
    );
  }
}
