import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:strike_flutter/models/model.dart';

class Settings extends StatelessWidget {
  const Settings({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: const SettingsForm(),
    );
  }
}

class SettingsForm extends StatefulWidget {
  const SettingsForm({super.key});

  @override
  State<SettingsForm> createState() => _SettingsFormState();
}

class _SettingsFormState extends State<SettingsForm> {
  final _formKey = GlobalKey<FormState>();

  final serverController = TextEditingController();
  late FormFieldState<bool> formFieldState;

  @override
  Widget build(BuildContext context) {
    var settings = context.watch<StrikeModel>();
    serverController.text = settings.host;

    return Form(
      key: _formKey,
      child: Column(
        children: [
          TextFormField(
            controller: serverController,
            autovalidateMode: AutovalidateMode.always,
            decoration: const InputDecoration(labelText: 'CANBell Server'),
            validator: (String? value) {
              if (value == null || value.isEmpty) {
                return 'Enter a valid IP address';
              }
              return null;
            },
          ),
          FormField<bool>(
            builder: (FormFieldState<bool> state) {
              formFieldState = state;
              return CheckboxListTile(
                title: const Text('The checkbox title'),
                controlAffinity: ListTileControlAffinity.leading,
                onChanged: (bool? checked) {
                  state.didChange(checked);
                },
                value: state.value ?? false,
              );
            },
          ),
          ElevatedButton(
            onPressed: () async {
              if (_formKey.currentState!.validate()) {
                var settings = context.read<StrikeModel>();

                settings.setPreferences(
                    host: serverController.text,
                    port: 80,
                    thresholdMs: 50,
                    alpha: 0.4,
                    beta: 0.1,
                    includeRounds: true,
                    showEstimates: false);
                settings.savePreferences();
              }
              Navigator.pop(context, formFieldState.value);
            },
            child: const Text('Submit'),
          ),
        ],
      ),
    );
  }
}
