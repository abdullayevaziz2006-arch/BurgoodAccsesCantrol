import 'package:flutter/material.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../data/models/access_log.dart';
import '../view_models/dashboard_view_model.dart';

class DashboardView extends StatelessWidget {
  const DashboardView({
    super.key,
    required this.viewModel,
    required this.serverUrl,
    required this.orgName,
  });

  final DashboardViewModel viewModel;
  final String serverUrl;
  final String orgName;

  Future<void> _openDoor(BuildContext context, int deviceId, String name) async {
    final msg = await viewModel.openDoor(deviceId);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('$name: $msg')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: viewModel,
      builder: (context, _) {
        final stats = viewModel.stats;
        final onlineDevices =
            viewModel.devices.where((d) => d.isOnline || d.isActive).toList();

        return RefreshIndicator(
          onRefresh: viewModel.loadAll,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (viewModel.errorMessage != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Card(
                    color: AppTheme.danger.withValues(alpha: 0.08),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Row(
                        children: [
                          const Icon(Icons.error_outline, color: AppTheme.danger),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              viewModel.errorMessage!,
                              style: const TextStyle(color: AppTheme.danger),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 1.55,
                children: [
                  _StatCard(
                    title: 'Jami xodimlar',
                    value: '${stats.totalUsers}',
                    icon: Icons.people_outline,
                    color: AppTheme.primary,
                  ),
                  _StatCard(
                    title: 'Bugungi kirishlar',
                    value: '${stats.todayEntries}',
                    icon: Icons.login_rounded,
                    color: AppTheme.success,
                  ),
                  _StatCard(
                    title: 'Hozir ichkarida',
                    value: '${stats.uniquePresent}',
                    icon: Icons.verified_user_outlined,
                    color: AppTheme.info,
                  ),
                  _StatCard(
                    title: 'Faol turniketlar',
                    value: '${stats.onlineDevices} / ${stats.totalDevices}',
                    icon: Icons.door_sliding_outlined,
                    color: AppTheme.warning,
                  ),
                ],
              ),
              if (onlineDevices.isNotEmpty) ...[
                const SizedBox(height: 20),
                const Text(
                  'Tezkor eshik ochish',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.textPrimary,
                  ),
                ),
                const SizedBox(height: 10),
                SizedBox(
                  height: 46,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: onlineDevices.length,
                    separatorBuilder: (_, _) => const SizedBox(width: 8),
                    itemBuilder: (context, index) {
                      final device = onlineDevices[index];
                      return FilledButton.tonalIcon(
                        onPressed: () =>
                            _openDoor(context, device.id, device.name),
                        icon: Icon(
                          Icons.lock_open_rounded,
                          size: 18,
                          color: device.isOnline
                              ? AppTheme.success
                              : AppTheme.textSecondary,
                        ),
                        label: Text(device.name),
                      );
                    },
                  ),
                ),
              ],
              const SizedBox(height: 22),
              Row(
                children: [
                  const Text(
                    'Jonli o\'tishlar',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    width: 8,
                    height: 8,
                    decoration: const BoxDecoration(
                      color: AppTheme.success,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const Spacer(),
                  if (viewModel.isLoading)
                    const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                ],
              ),
              const SizedBox(height: 10),
              if (viewModel.liveLogs.isEmpty && !viewModel.isLoading)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Center(
                      child: Text(
                        'Hozircha o\'tishlar qayd etilmagan',
                        style: TextStyle(color: AppTheme.textSecondary),
                      ),
                    ),
                  ),
                )
              else
                ...viewModel.liveLogs.map(
                  (log) => _LiveLogTile(log: log, serverUrl: serverUrl),
                ),
            ],
          ),
        );
      },
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  final String title;
  final String value;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppTheme.textSecondary,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                Icon(icon, size: 18, color: color),
              ],
            ),
            Text(
              value,
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w700,
                color: AppTheme.textPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LiveLogTile extends StatelessWidget {
  const _LiveLogTile({
    required this.log,
    required this.serverUrl,
  });

  final AccessLog log;
  final String serverUrl;

  @override
  Widget build(BuildContext context) {
    final imageUrl = AppConstants.resolveMediaUrl(
      serverUrl,
      log.snapshotUrl ?? log.photoPath,
    );
    final isEntry = log.direction == 'entry' || log.direction == 'break_in';
    final badgeColor = isEntry ? AppTheme.success : AppTheme.warning;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: AppTheme.primary.withValues(alpha: 0.1),
          backgroundImage: imageUrl.isNotEmpty ? NetworkImage(imageUrl) : null,
          child: imageUrl.isEmpty
              ? const Icon(Icons.person, color: AppTheme.primary)
              : null,
        ),
        title: Text(
          log.userName ?? log.employeeNo ?? 'Noma\'lum shaxs',
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Text(
          '${log.deviceName ?? 'Turniket'} • ${log.formattedTime}',
          style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
        ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
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
  }
}
