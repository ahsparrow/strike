import 'dart:io';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:strike_flutter/models/model.dart';

// Settings screen
class Settings extends StatelessWidget {
  const Settings({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: const Padding(
        padding: EdgeInsets.all(16),
        child: SettingsForm(),
      ),
    );
  }
}

// Settings form
class SettingsForm extends StatefulWidget {
  const SettingsForm({super.key});

  @override
  State<SettingsForm> createState() => _SettingsFormState();
}

// Settings form state
class _SettingsFormState extends State<SettingsForm> {
  final _formKey = GlobalKey<FormState>();

  // State controllers for each setting
  final hostController = TextEditingController();
  final portController = TextEditingController();
  final thresholdController = TextEditingController();
  final alphaController = TextEditingController();
  final betaController = TextEditingController();
  late FormFieldState<bool> estimatesState;
  late FormFieldState<bool> roundsState;

  @override
  Widget build(BuildContext context) {
    var settings = context.watch<StrikeModel>();

    hostController.text = settings.host;
    portController.text = settings.port.toString();
    thresholdController.text = settings.thresholdMs.toString();
    alphaController.text = settings.alpha.toString();
    betaController.text = settings.beta.toString();

    return Form(
      key: _formKey,
      child: Column(
        children: [
          // CANBell host
          TextFormField(
            controller: hostController,
            autovalidateMode: AutovalidateMode.always,
            decoration: const InputDecoration(
              labelText: 'CANBell Host',
              border: OutlineInputBorder(),
            ),
            validator: (String? value) {
              var ipAddress = InternetAddress.tryParse(value ?? '');
              if (ipAddress == null) {
                return 'Enter a valid IP address';
              }
              return null;
            },
          ),
          const SizedBox(height: 16),

          // CANBell port
          TextFormField(
            controller: portController,
            autovalidateMode: AutovalidateMode.always,
            decoration: const InputDecoration(
              labelText: 'CANBell port',
              border: OutlineInputBorder(),
            ),
            validator: (String? value) {
              var port = int.tryParse(value ?? '');
              if (port == null || port <= 0) {
                return 'Enter an integer > 0';
              }
              return null;
            },
          ),
          const SizedBox(height: 16),

          // Error threshold
          TextFormField(
            controller: thresholdController,
            autovalidateMode: AutovalidateMode.always,
            decoration: const InputDecoration(
              labelText: 'Threshold (ms)',
              border: OutlineInputBorder(),
            ),
            validator: (String? value) {
              var threshold = int.tryParse(value ?? '');
              if (threshold == null || threshold <= 0) {
                return 'Enter an integer > 0';
              }
              return null;
            },
          ),
          const SizedBox(height: 16),

          // Alpha filter coefficient
          TextFormField(
            controller: alphaController,
            autovalidateMode: AutovalidateMode.always,
            decoration: const InputDecoration(
              labelText: 'Alpha',
              border: OutlineInputBorder(),
            ),
            validator: (String? value) {
              var alpha = double.tryParse(value ?? '');
              if (alpha == null || alpha <= 0) {
                return 'Enter a number < 0';
              }
              return null;
            },
          ),
          const SizedBox(height: 16),

          // Beta filter coefficient
          TextFormField(
            controller: betaController,
            autovalidateMode: AutovalidateMode.always,
            decoration: const InputDecoration(
              labelText: 'Beta',
              border: OutlineInputBorder(),
            ),
            validator: (String? value) {
              var beta = double.tryParse(value ?? '');
              if (beta == null || beta <= 0) {
                return 'Enter a number < 0';
              }
              return null;
            },
          ),
          const SizedBox(height: 16),

          // Include rounds
          FormField<bool>(
            builder: (FormFieldState<bool> state) {
              roundsState = state;

              return CheckboxListTile(
                title: const Text('Include rounds'),
                controlAffinity: ListTileControlAffinity.leading,
                onChanged: (bool? checked) {
                  state.didChange(checked);
                },
                value: state.value ?? false,
              );
            },
            initialValue: settings.includeRounds,
          ),

          // Show estimates
          FormField<bool>(
            builder: (FormFieldState<bool> state) {
              estimatesState = state;

              return CheckboxListTile(
                title: const Text('Show estimates'),
                controlAffinity: ListTileControlAffinity.leading,
                onChanged: (bool? checked) {
                  state.didChange(checked);
                },
                value: state.value ?? false,
              );
            },
            initialValue: settings.showEstimates,
          ),
          const SizedBox(height: 16),

          Row(
            children: [
              OutlinedButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                child: const Text('Cancel'),
              ),
              const Spacer(),
              FilledButton(
                onPressed: () async {
                  if (_formKey.currentState!.validate()) {
                    var settings = context.read<StrikeModel>();

                    // Update settings and save
                    settings.setPreferences(
                        host: hostController.text,
                        port: int.parse(portController.text),
                        thresholdMs: int.parse(thresholdController.text),
                        alpha: double.parse(alphaController.text),
                        beta: double.parse(betaController.text),
                        includeRounds: roundsState.value ?? false,
                        showEstimates: estimatesState.value ?? false);
                    settings.savePreferences();

                    Navigator.pop(context);
                  }
                },
                child: const Text('Save'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
