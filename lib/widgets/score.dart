import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:strike_flutter/models/model.dart';

class ScoreWidget extends StatelessWidget {
  const ScoreWidget({super.key});

  @override
  Widget build(context) {
    return Center(
      child: Consumer<StrikeModel>(
        builder: (context, strikeData, child) => Text(
          '${strikeData.touchNum}',
        ),
      ),
    );
  }
}
