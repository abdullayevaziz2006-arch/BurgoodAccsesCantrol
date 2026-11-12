import 'package:flutter/material.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../view_models/auth_view_model.dart';

class LoginView extends StatefulWidget {
  const LoginView({
    super.key,
    required this.viewModel,
  });

  final AuthViewModel viewModel;

  @override
  State<LoginView> createState() => _LoginViewState();
}

class _LoginViewState extends State<LoginView> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  late final TextEditingController _serverController;

  bool _obscurePassword = true;
  bool _showServerConfig = false;

  @override
  void initState() {
    super.initState();
    _serverController = TextEditingController(
      text: widget.viewModel.serverUrl.isNotEmpty
          ? widget.viewModel.serverUrl
          : AppConstants.defaultServerUrl,
    );
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _serverController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    FocusScope.of(context).unfocus();
    await widget.viewModel.login(
      username: _usernameController.text.trim(),
      password: _passwordController.text,
      serverUrl: _serverController.text.trim(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: ListenableBuilder(
                listenable: widget.viewModel,
                builder: (context, _) {
                  final vm = widget.viewModel;
                  return Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Container(
                          width: 68,
                          height: 68,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: AppTheme.primary.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: const Icon(
                            Icons.shield_outlined,
                            size: 36,
                            color: AppTheme.primary,
                          ),
                        ),
                        const SizedBox(height: 20),
                        const Text(
                          'Burgood Access Control',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 6),
                        const Text(
                          'Kirish-chiqish va turniket nazorati',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 14,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 28),
                        Card(
                          child: Padding(
                            padding: const EdgeInsets.all(20),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                TextFormField(
                                  controller: _usernameController,
                                  textInputAction: TextInputAction.next,
                                  decoration: const InputDecoration(
                                    labelText: 'Login (username)',
                                    prefixIcon: Icon(Icons.person_outline),
                                  ),
                                  validator: (value) {
                                    if (value == null || value.trim().isEmpty) {
                                      return 'Loginni kiriting';
                                    }
                                    return null;
                                  },
                                ),
                                const SizedBox(height: 14),
                                TextFormField(
                                  controller: _passwordController,
                                  obscureText: _obscurePassword,
                                  textInputAction: TextInputAction.done,
                                  onFieldSubmitted: (_) => _submit(),
                                  decoration: InputDecoration(
                                    labelText: 'Parol',
                                    prefixIcon: const Icon(Icons.lock_outline),
                                    suffixIcon: IconButton(
                                      onPressed: () {
                                        setState(() {
                                          _obscurePassword = !_obscurePassword;
                                        });
                                      },
                                      icon: Icon(
                                        _obscurePassword
                                            ? Icons.visibility_outlined
                                            : Icons.visibility_off_outlined,
                                      ),
                                    ),
                                  ),
                                  validator: (value) {
                                    if (value == null || value.isEmpty) {
                                      return 'Parolni kiriting';
                                    }
                                    return null;
                                  },
                                ),
                                const SizedBox(height: 10),
                                Align(
                                  alignment: Alignment.centerRight,
                                  child: TextButton.icon(
                                    onPressed: () {
                                      setState(() {
                                        _showServerConfig = !_showServerConfig;
                                      });
                                    },
                                    icon: Icon(
                                      _showServerConfig
                                          ? Icons.expand_less
                                          : Icons.dns_outlined,
                                      size: 18,
                                    ),
                                    label: Text(
                                      _showServerConfig
                                          ? 'Server manzilini yashirish'
                                          : 'Server manzilini sozlash',
                                      style: const TextStyle(fontSize: 13),
                                    ),
                                  ),
                                ),
                                if (_showServerConfig) ...[
                                  const SizedBox(height: 6),
                                  TextFormField(
                                    controller: _serverController,
                                    keyboardType: TextInputType.url,
                                    decoration: const InputDecoration(
                                      labelText: 'Server URL',
                                      hintText: AppConstants.defaultServerUrl,
                                      prefixIcon: Icon(Icons.link),
                                    ),
                                    validator: (value) {
                                      final text = value?.trim() ?? '';
                                      if (text.isEmpty ||
                                          (!text.startsWith('http://') &&
                                              !text.startsWith('https://'))) {
                                        return 'http:// yoki https:// bilan boshlanuvchi manzil kiriting';
                                      }
                                      return null;
                                    },
                                  ),
                                ],
                                if (vm.errorMessage != null) ...[
                                  const SizedBox(height: 14),
                                  Container(
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: AppTheme.danger
                                          .withValues(alpha: 0.08),
                                      borderRadius: BorderRadius.circular(10),
                                      border: Border.all(
                                        color: AppTheme.danger
                                            .withValues(alpha: 0.3),
                                      ),
                                    ),
                                    child: Row(
                                      children: [
                                        const Icon(
                                          Icons.error_outline,
                                          color: AppTheme.danger,
                                          size: 20,
                                        ),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: Text(
                                            vm.errorMessage!,
                                            style: const TextStyle(
                                              color: AppTheme.danger,
                                              fontSize: 13,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                                const SizedBox(height: 20),
                                FilledButton(
                                  onPressed: vm.isLoading ? null : _submit,
                                  child: vm.isLoading
                                      ? const SizedBox(
                                          height: 20,
                                          width: 20,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                            color: Colors.white,
                                          ),
                                        )
                                      : const Text('Kirish'),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}
