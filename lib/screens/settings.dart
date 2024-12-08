import 'package:flutter/material.dart';

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

  final controller = TextEditingController();
  late FormFieldState<bool> formFieldState;

  @override
  initState() {
    super.initState();
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          TextFormField(
            controller: controller,
            autovalidateMode: AutovalidateMode.always,
            decoration: const InputDecoration(labelText: 'CANBell Server'),
            validator: (String? value) {
              if (value == null || value.isEmpty) {
                return 'Enter some text you bozo';
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
              if (_formKey.currentState!.validate()) {}
              Navigator.pop(context, formFieldState.value);
            },
            child: const Text('Submit'),
          ),
        ],
      ),
    );
  }
}
