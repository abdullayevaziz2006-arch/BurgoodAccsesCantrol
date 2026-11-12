import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../attendance/view_models/attendance_view_model.dart';
import '../../attendance/views/attendance_view.dart';
import '../../auth/view_models/auth_view_model.dart';
import '../../dashboard/view_models/dashboard_view_model.dart';
import '../../dashboard/views/dashboard_view.dart';
import '../../devices/view_models/devices_view_model.dart';
import '../../devices/views/devices_view.dart';
import '../../staff/view_models/staff_view_model.dart';
import '../../staff/views/staff_list_view.dart';

class HomeShellView extends StatefulWidget {
  const HomeShellView({
    super.key,
    required this.authViewModel,
    required this.dashboardViewModel,
    required this.staffViewModel,
    required this.attendanceViewModel,
    required this.devicesViewModel,
  });

  final AuthViewModel authViewModel;
  final DashboardViewModel dashboardViewModel;
  final StaffViewModel staffViewModel;
  final AttendanceViewModel attendanceViewModel;
  final DevicesViewModel devicesViewModel;

  @override
  State<HomeShellView> createState() => _HomeShellViewState();
}

class _HomeShellViewState extends State<HomeShellView> {
  int _selectedIndex = 0;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  void _loadInitialData() {
    final user = widget.authViewModel.user;
    if (user == null) return;

    if (user.isManagerOrAdmin) {
      widget.dashboardViewModel
          .startLiveUpdates(widget.authViewModel.serverUrl);
      widget.dashboardViewModel.loadAll();
      widget.staffViewModel.loadUsers();
      widget.attendanceViewModel.loadLogs();
      widget.devicesViewModel.loadDevices();
    } else {
      widget.attendanceViewModel.loadLogs(onlyUserId: user.id);
    }
  }

  Future<void> _confirmLogout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Chiqish'),
        content: const Text('Hisobdan chiqishni xohlaysizmi?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Bekor qilish'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: FilledButton.styleFrom(backgroundColor: AppTheme.danger),
            child: const Text('Chiqish'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await widget.authViewModel.logout();
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = widget.authViewModel.user;
    final org = widget.authViewModel.organization;
    final isManager = user?.isManagerOrAdmin ?? false;

    if (!isManager) {
      final employeePages = [
        AttendanceView(
          viewModel: widget.attendanceViewModel,
          serverUrl: widget.authViewModel.serverUrl,
          onlyUserId: user?.id,
        ),
        _ProfileView(
          authViewModel: widget.authViewModel,
          onLogout: _confirmLogout,
        ),
      ];

      final safeIndex = _selectedIndex.clamp(0, employeePages.length - 1);

      return Scaffold(
        appBar: AppBar(
          title: Text(org?.name ?? 'Burgood Access'),
          actions: [
            IconButton(
              onPressed: _confirmLogout,
              icon: const Icon(Icons.logout_outlined),
              tooltip: 'Chiqish',
            ),
          ],
        ),
        body: IndexedStack(
          index: safeIndex,
          children: employeePages,
        ),
        bottomNavigationBar: NavigationBar(
          selectedIndex: safeIndex,
          onDestinationSelected: (index) => setState(() => _selectedIndex = index),
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.fact_check_outlined),
              selectedIcon: Icon(Icons.fact_check),
              label: 'Davomatim',
            ),
            NavigationDestination(
              icon: Icon(Icons.person_outline),
              selectedIcon: Icon(Icons.person),
              label: 'Profil',
            ),
          ],
        ),
      );
    }

    final managerPages = [
      DashboardView(
        viewModel: widget.dashboardViewModel,
        serverUrl: widget.authViewModel.serverUrl,
        orgName: org?.name ?? 'Burgood Access',
      ),
      StaffListView(
        viewModel: widget.staffViewModel,
        serverUrl: widget.authViewModel.serverUrl,
      ),
      AttendanceView(
        viewModel: widget.attendanceViewModel,
        serverUrl: widget.authViewModel.serverUrl,
      ),
      DevicesView(
        viewModel: widget.devicesViewModel,
      ),
    ];

    final titles = [
      org?.name ?? 'Bosh sahifa',
      'Xodimlar',
      'Davomat jurnali',
      'Turniketlar',
    ];

    final safeIndex = _selectedIndex.clamp(0, managerPages.length - 1);

    return Scaffold(
      appBar: AppBar(
        title: Text(titles[safeIndex]),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 4),
            child: Center(
              child: Text(
                user?.fullName ?? '',
                style: const TextStyle(
                  fontSize: 13,
                  color: AppTheme.textSecondary,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),
          IconButton(
            onPressed: _confirmLogout,
            icon: const Icon(Icons.logout_outlined),
            tooltip: 'Chiqish',
          ),
        ],
      ),
      body: IndexedStack(
        index: safeIndex,
        children: managerPages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: safeIndex,
        onDestinationSelected: (index) => setState(() => _selectedIndex = index),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Asosiy',
          ),
          NavigationDestination(
            icon: Icon(Icons.people_outline),
            selectedIcon: Icon(Icons.people),
            label: 'Xodimlar',
          ),
          NavigationDestination(
            icon: Icon(Icons.fact_check_outlined),
            selectedIcon: Icon(Icons.fact_check),
            label: 'Davomat',
          ),
          NavigationDestination(
            icon: Icon(Icons.door_sliding_outlined),
            selectedIcon: Icon(Icons.door_sliding),
            label: 'Turniket',
          ),
        ],
      ),
    );
  }
}

class _ProfileView extends StatelessWidget {
  const _ProfileView({
    required this.authViewModel,
    required this.onLogout,
  });

  final AuthViewModel authViewModel;
  final VoidCallback onLogout;

  @override
  Widget build(BuildContext context) {
    final user = authViewModel.user;
    final org = authViewModel.organization;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                CircleAvatar(
                  radius: 34,
                  backgroundColor: AppTheme.primary.withValues(alpha: 0.12),
                  child: const Icon(
                    Icons.person,
                    size: 36,
                    color: AppTheme.primary,
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  user?.fullName ?? 'Foydalanuvchi',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '@${user?.username ?? ''} • ${user?.role ?? ''}',
                  style: const TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 13,
                  ),
                ),
                if (org != null) ...[
                  const SizedBox(height: 8),
                  Chip(label: Text(org.name)),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Card(
          child: ListTile(
            leading: const Icon(Icons.dns_outlined),
            title: const Text('Server manzili'),
            subtitle: Text(authViewModel.serverUrl),
          ),
        ),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: onLogout,
          icon: const Icon(Icons.logout, color: AppTheme.danger),
          label: const Text(
            'Hisobdan chiqish',
            style: TextStyle(color: AppTheme.danger),
          ),
        ),
      ],
    );
  }
}
