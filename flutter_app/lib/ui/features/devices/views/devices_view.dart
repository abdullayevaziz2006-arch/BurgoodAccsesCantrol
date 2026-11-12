import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../view_models/devices_view_model.dart';

class DevicesView extends StatelessWidget {
  const DevicesView({
    super.key,
    required this.viewModel,
  });

  final DevicesViewModel viewModel;

  Future<void> _testConnection(
    BuildContext context,
    int deviceId,
    String name,
  ) async {
    final (ok, msg) = await viewModel.testConnection(deviceId);
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$name: $msg'),
        backgroundColor: ok ? AppTheme.success : AppTheme.danger,
      ),
    );
  }

  Future<void> _openDoor(
    BuildContext context,
    int deviceId,
    String name,
  ) async {
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
        final devices = viewModel.devices;

        return RefreshIndicator(
          onRefresh: viewModel.loadDevices,
          child: viewModel.isLoading && devices.isEmpty
              ? const Center(child: CircularProgressIndicator())
              : devices.isEmpty
                  ? ListView(
                      children: const [
                        SizedBox(height: 80),
                        Center(
                          child: Text(
                            'Turniketlar topilmadi',
                            style: TextStyle(color: AppTheme.textSecondary),
                          ),
                        ),
                      ],
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: devices.length,
                      itemBuilder: (context, index) {
                        final device = devices[index];
                        final statusColor =
                            device.isOnline ? AppTheme.success : AppTheme.danger;

                        return Card(
                          margin: const EdgeInsets.only(bottom: 12),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.all(10),
                                      decoration: BoxDecoration(
                                        color: AppTheme.primary
                                            .withValues(alpha: 0.1),
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: const Icon(
                                        Icons.door_sliding_outlined,
                                        color: AppTheme.primary,
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            device.name,
                                            style: const TextStyle(
                                              fontSize: 16,
                                              fontWeight: FontWeight.w700,
                                            ),
                                          ),
                                          const SizedBox(height: 2),
                                          Text(
                                            '${device.ipAddress}:${device.port} • ${device.directionLabel}',
                                            style: const TextStyle(
                                              fontSize: 12,
                                              color: AppTheme.textSecondary,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 10,
                                        vertical: 5,
                                      ),
                                      decoration: BoxDecoration(
                                        color:
                                            statusColor.withValues(alpha: 0.12),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Text(
                                        device.isOnline ? 'Online' : 'Offline',
                                        style: TextStyle(
                                          color: statusColor,
                                          fontSize: 12,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 12),
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 8,
                                  children: [
                                    if (device.isUniversal)
                                      const Chip(label: Text('Universal')),
                                    if (device.isLunchTerminal)
                                      const Chip(label: Text('Tushlik terminali')),
                                    if (device.location != null &&
                                        device.location!.isNotEmpty)
                                      Chip(label: Text(device.location!)),
                                  ],
                                ),
                                const SizedBox(height: 12),
                                Row(
                                  children: [
                                    Expanded(
                                      child: OutlinedButton.icon(
                                        onPressed: () => _testConnection(
                                          context,
                                          device.id,
                                          device.name,
                                        ),
                                        icon: const Icon(Icons.wifi_tethering,
                                            size: 18),
                                        label: const Text('Aloqani tekshirish'),
                                      ),
                                    ),
                                    const SizedBox(width: 10),
                                    Expanded(
                                      child: FilledButton.icon(
                                        onPressed: () => _openDoor(
                                          context,
                                          device.id,
                                          device.name,
                                        ),
                                        icon: const Icon(
                                            Icons.lock_open_rounded,
                                            size: 18),
                                        label: const Text('Eshikni ochish'),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
        );
      },
    );
  }
}
