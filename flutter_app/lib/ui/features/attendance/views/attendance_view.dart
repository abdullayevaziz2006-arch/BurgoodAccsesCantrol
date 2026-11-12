import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../view_models/attendance_view_model.dart';

class AttendanceView extends StatelessWidget {
  const AttendanceView({
    super.key,
    required this.viewModel,
    required this.serverUrl,
    this.onlyUserId,
  });

  final AttendanceViewModel viewModel;
  final String serverUrl;
  final int? onlyUserId;

  Future<void> _pickDate(BuildContext context) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: viewModel.selectedDate,
      firstDate: DateTime(2023),
      lastDate: DateTime.now().add(const Duration(days: 1)),
    );
    if (picked != null) {
      viewModel.setDate(picked);
      await viewModel.loadLogs(onlyUserId: onlyUserId);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: viewModel,
      builder: (context, _) {
        final logs = viewModel.visibleLogs;
        final dateLabel = DateFormat('dd.MM.yyyy').format(viewModel.selectedDate);

        return Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      onChanged: viewModel.setSearch,
                      decoration: const InputDecoration(
                        hintText: 'Ism, ID yoki qurilma...',
                        prefixIcon: Icon(Icons.search),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  OutlinedButton.icon(
                    onPressed: () => _pickDate(context),
                    icon: const Icon(Icons.calendar_today_outlined, size: 18),
                    label: Text(dateLabel),
                  ),
                ],
              ),
            ),
            SizedBox(
              height: 44,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: [
                  _FilterChip(
                    label: 'Barchasi',
                    selected: viewModel.directionFilter == null,
                    onTap: () => viewModel.setDirectionFilter(null),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'Kirish',
                    selected: viewModel.directionFilter == 'entry',
                    onTap: () => viewModel.setDirectionFilter('entry'),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'Chiqish',
                    selected: viewModel.directionFilter == 'exit',
                    onTap: () => viewModel.setDirectionFilter('exit'),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'Tushlikka chiqish',
                    selected: viewModel.directionFilter == 'break_out',
                    onTap: () => viewModel.setDirectionFilter('break_out'),
                  ),
                  const SizedBox(width: 8),
                  _FilterChip(
                    label: 'Tushlikdan qaytish',
                    selected: viewModel.directionFilter == 'break_in',
                    onTap: () => viewModel.setDirectionFilter('break_in'),
                  ),
                ],
              ),
            ),
            if (viewModel.errorMessage != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                child: Text(
                  viewModel.errorMessage!,
                  style: const TextStyle(color: AppTheme.danger, fontSize: 13),
                ),
              ),
            Expanded(
              child: RefreshIndicator(
                onRefresh: () => viewModel.loadLogs(onlyUserId: onlyUserId),
                child: viewModel.isLoading && logs.isEmpty
                    ? const Center(child: CircularProgressIndicator())
                    : logs.isEmpty
                        ? ListView(
                            children: const [
                              SizedBox(height: 80),
                              Center(
                                child: Text(
                                  'Tanlangan kun uchun yozuvlar yo\'q',
                                  style: TextStyle(color: AppTheme.textSecondary),
                                ),
                              ),
                            ],
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: logs.length,
                            itemBuilder: (context, index) {
                              final log = logs[index];
                              final imageUrl = AppConstants.resolveMediaUrl(
                                serverUrl,
                                log.snapshotUrl ?? log.photoPath,
                              );
                              final isEntry = log.direction == 'entry' ||
                                  log.direction == 'break_in';
                              final badgeColor =
                                  isEntry ? AppTheme.success : AppTheme.warning;

                              return Card(
                                margin: const EdgeInsets.only(bottom: 8),
                                child: ListTile(
                                  leading: CircleAvatar(
                                    backgroundColor:
                                        AppTheme.primary.withValues(alpha: 0.1),
                                    backgroundImage: imageUrl.isNotEmpty
                                        ? NetworkImage(imageUrl)
                                        : null,
                                    child: imageUrl.isEmpty
                                        ? const Icon(
                                            Icons.person,
                                            color: AppTheme.primary,
                                          )
                                        : null,
                                  ),
                                  title: Text(
                                    log.userName ??
                                        log.employeeNo ??
                                        'Noma\'lum',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                  subtitle: Text(
                                    '${log.deviceName ?? 'Turniket'} • ${log.formattedDate} ${log.formattedTime}',
                                    style: const TextStyle(
                                      fontSize: 12,
                                      color: AppTheme.textSecondary,
                                    ),
                                  ),
                                  trailing: Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 10,
                                      vertical: 5,
                                    ),
                                    decoration: BoxDecoration(
                                      color: badgeColor.withValues(alpha: 0.12),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text(
                                      log.displayDirection,
                                      style: TextStyle(
                                        color: badgeColor,
                                        fontSize: 12,
                                        fontWeight: FontWeight.w600,
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
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) => onTap(),
    );
  }
}
