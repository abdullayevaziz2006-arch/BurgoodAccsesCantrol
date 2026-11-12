import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../../../core/theme/app_theme.dart';
import '../view_models/staff_view_model.dart';

class AddStaffSheet extends StatefulWidget {
  const AddStaffSheet({
    super.key,
    required this.viewModel,
  });

  final StaffViewModel viewModel;

  @override
  State<AddStaffSheet> createState() => _AddStaffSheetState();
}

class _AddStaffSheetState extends State<AddStaffSheet> {
  final _formKey = GlobalKey<FormState>();
  final _fullNameController = TextEditingController();
  final _employeeNoController = TextEditingController();
  final _positionController = TextEditingController();
  final _phoneController = TextEditingController();
  final _picker = ImagePicker();

  String _role = 'staff';
  bool _syncToTerminal = true;
  Uint8List? _photoBytes;
  String? _photoFilename;

  @override
  void dispose() {
    _fullNameController.dispose();
    _employeeNoController.dispose();
    _positionController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _pickImage(ImageSource source) async {
    final file = await _picker.pickImage(
      source: source,
      maxWidth: 1024,
      maxHeight: 1024,
      imageQuality: 85,
    );
    if (file == null) return;
    final bytes = await file.readAsBytes();
    if (!mounted) return;
    setState(() {
      _photoBytes = bytes;
      _photoFilename = file.name;
    });
  }

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    final ok = await widget.viewModel.addStaffMember(
      fullName: _fullNameController.text.trim(),
      employeeNo: _employeeNoController.text.trim(),
      role: _role,
      position: _positionController.text.trim().isEmpty
          ? null
          : _positionController.text.trim(),
      phoneNumber: _phoneController.text.trim().isEmpty
          ? null
          : _phoneController.text.trim(),
      photoBytes: _photoBytes,
      photoFilename: _photoFilename,
      syncToTerminal: _syncToTerminal,
    );

    if (ok && mounted) {
      Navigator.of(context).pop(true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return Padding(
      padding: EdgeInsets.fromLTRB(20, 16, 20, 20 + bottomInset),
      child: ListenableBuilder(
        listenable: widget.viewModel,
        builder: (context, _) {
          final vm = widget.viewModel;

          return SingleChildScrollView(
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Yangi xodim qo\'shish',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      IconButton(
                        onPressed: () => Navigator.of(context).pop(false),
                        icon: const Icon(Icons.close),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 34,
                        backgroundColor: AppTheme.primary.withValues(alpha: 0.1),
                        backgroundImage:
                            _photoBytes != null ? MemoryImage(_photoBytes!) : null,
                        child: _photoBytes == null
                            ? const Icon(
                                Icons.person_outline,
                                size: 32,
                                color: AppTheme.primary,
                              )
                            : null,
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            OutlinedButton.icon(
                              onPressed: () => _pickImage(ImageSource.camera),
                              icon: const Icon(Icons.camera_alt_outlined, size: 18),
                              label: const Text('Kamera'),
                            ),
                            OutlinedButton.icon(
                              onPressed: () => _pickImage(ImageSource.gallery),
                              icon: const Icon(Icons.photo_library_outlined, size: 18),
                              label: const Text('Galereya'),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _fullNameController,
                    decoration: const InputDecoration(
                      labelText: 'F.I.O *',
                    ),
                    validator: (v) => (v == null || v.trim().isEmpty)
                        ? 'F.I.O ni kiriting'
                        : null,
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _employeeNoController,
                    decoration: const InputDecoration(
                      labelText: 'Xodim ID (employeeNo) *',
                    ),
                    validator: (v) => (v == null || v.trim().isEmpty)
                        ? 'Xodim ID ni kiriting'
                        : null,
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: _role,
                    decoration: const InputDecoration(labelText: 'Rol'),
                    items: const [
                      DropdownMenuItem(value: 'staff', child: Text('Xodim (Staff)')),
                      DropdownMenuItem(value: 'student', child: Text('Talaba (Student)')),
                      DropdownMenuItem(value: 'manager', child: Text('Menejer (Manager)')),
                    ],
                    onChanged: (val) {
                      if (val != null) setState(() => _role = val);
                    },
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _positionController,
                    decoration: const InputDecoration(
                      labelText: 'Lavozimi',
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _phoneController,
                    keyboardType: TextInputType.phone,
                    decoration: const InputDecoration(
                      labelText: 'Telefon raqami',
                    ),
                  ),
                  const SizedBox(height: 8),
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Turniketlarga sinxronlash'),
                    subtitle: const Text(
                      'Saqlangandan so\'ng barcha qurilmalarga yuborish',
                      style: TextStyle(fontSize: 12),
                    ),
                    value: _syncToTerminal,
                    onChanged: (val) => setState(() => _syncToTerminal = val),
                  ),
                  if (vm.errorMessage != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      vm.errorMessage!,
                      style: const TextStyle(color: AppTheme.danger, fontSize: 13),
                    ),
                  ],
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: vm.isSaving ? null : _save,
                    child: vm.isSaving
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text('Saqlash'),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
