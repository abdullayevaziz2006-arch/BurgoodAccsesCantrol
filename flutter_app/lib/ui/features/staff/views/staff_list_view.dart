import 'package:flutter/material.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../view_models/staff_view_model.dart';
import 'add_staff_sheet.dart';

class StaffListView extends StatelessWidget {
  const StaffListView({
    super.key,
    required this.viewModel,
    required this.serverUrl,
  });

  final StaffViewModel viewModel;
  final String serverUrl;

  Future<void> _openAddStaff(BuildContext context) async {
    final added = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => AddStaffSheet(viewModel: viewModel),
    );

    if (added == true && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Xodim muvaffaqiyatli qo\'shildi')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ListenableBuilder(
        listenable: viewModel,
        builder: (context, _) {
          final users = viewModel.filteredUsers;

          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                child: TextField(
                  onChanged: viewModel.setSearch,
                  decoration: const InputDecoration(
                    hintText: 'Ism, ID yoki lavozim bo\'yicha qidirish...',
                    prefixIcon: Icon(Icons.search),
                  ),
                ),
              ),
              if (viewModel.errorMessage != null)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  child: Text(
                    viewModel.errorMessage!,
                    style: const TextStyle(color: AppTheme.danger, fontSize: 13),
                  ),
                ),
              Expanded(
                child: RefreshIndicator(
                  onRefresh: viewModel.loadUsers,
                  child: viewModel.isLoading && users.isEmpty
                      ? const Center(child: CircularProgressIndicator())
                      : users.isEmpty
                          ? ListView(
                              children: const [
                                SizedBox(height: 80),
                                Center(
                                  child: Text(
                                    'Xodimlar topilmadi',
                                    style: TextStyle(color: AppTheme.textSecondary),
                                  ),
                                ),
                              ],
                            )
                          : ListView.builder(
                              padding: const EdgeInsets.fromLTRB(16, 4, 16, 84),
                              itemCount: users.length,
                              itemBuilder: (context, index) {
                                final staff = users[index];
                                final photoUrl = AppConstants.resolveMediaUrl(
                                  serverUrl,
                                  staff.photoPath,
                                );

                                return Card(
                                  margin: const EdgeInsets.only(bottom: 8),
                                  child: ListTile(
                                    leading: CircleAvatar(
                                      backgroundColor:
                                          AppTheme.primary.withValues(alpha: 0.1),
                                      backgroundImage: photoUrl.isNotEmpty
                                          ? NetworkImage(photoUrl)
                                          : null,
                                      child: photoUrl.isEmpty
                                          ? Text(
                                              staff.fullName.isNotEmpty
                                                  ? staff.fullName[0].toUpperCase()
                                                  : '?',
                                              style: const TextStyle(
                                                color: AppTheme.primary,
                                                fontWeight: FontWeight.w700,
                                              ),
                                            )
                                          : null,
                                    ),
                                    title: Text(
                                      staff.fullName,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                    subtitle: Text(
                                      'ID: ${staff.employeeNo}'
                                      '${staff.position != null && staff.position!.isNotEmpty ? ' • ${staff.position}' : ''}',
                                      style: const TextStyle(
                                        fontSize: 12,
                                        color: AppTheme.textSecondary,
                                      ),
                                    ),
                                    trailing: Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 8,
                                        vertical: 4,
                                      ),
                                      decoration: BoxDecoration(
                                        color: staff.isActive
                                            ? AppTheme.success
                                                .withValues(alpha: 0.12)
                                            : AppTheme.danger
                                                .withValues(alpha: 0.12),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Text(
                                        staff.isActive ? 'Faol' : 'Nofaol',
                                        style: TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.w600,
                                          color: staff.isActive
                                              ? AppTheme.success
                                              : AppTheme.danger,
                                        ),
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                ),
              ),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openAddStaff(context),
        icon: const Icon(Icons.person_add_alt_1),
        label: const Text('Xodim qo\'shish'),
      ),
    );
  }
}
