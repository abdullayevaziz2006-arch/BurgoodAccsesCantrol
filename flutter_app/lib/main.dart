import 'package:flutter/material.dart';

import 'core/theme/app_theme.dart';
import 'data/repositories/access_repository.dart';
import 'data/repositories/auth_repository.dart';
import 'data/services/api_client.dart';
import 'data/services/storage_service.dart';
import 'data/services/websocket_service.dart';
import 'ui/features/attendance/view_models/attendance_view_model.dart';
import 'ui/features/auth/view_models/auth_view_model.dart';
import 'ui/features/auth/views/login_view.dart';
import 'ui/features/dashboard/view_models/dashboard_view_model.dart';
import 'ui/features/devices/view_models/devices_view_model.dart';
import 'ui/features/home/views/home_shell_view.dart';
import 'ui/features/staff/view_models/staff_view_model.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const BurgoodApp());
}

class BurgoodApp extends StatefulWidget {
  const BurgoodApp({super.key});

  @override
  State<BurgoodApp> createState() => _BurgoodAppState();
}

class _BurgoodAppState extends State<BurgoodApp> {
  late final StorageService _storageService;
  late final ApiClient _apiClient;
  late final WebSocketService _webSocketService;
  late final AuthRepository _authRepository;
  late final AccessRepository _accessRepository;

  late final AuthViewModel _authViewModel;
  late final DashboardViewModel _dashboardViewModel;
  late final StaffViewModel _staffViewModel;
  late final AttendanceViewModel _attendanceViewModel;
  late final DevicesViewModel _devicesViewModel;

  @override
  void initState() {
    super.initState();
    _storageService = StorageService();
    _apiClient = ApiClient(storageService: _storageService);
    _webSocketService = WebSocketService();
    _authRepository = AuthRepository(
      apiClient: _apiClient,
      storageService: _storageService,
    );
    _accessRepository = AccessRepository(apiClient: _apiClient);

    _authViewModel = AuthViewModel(authRepository: _authRepository);
    _dashboardViewModel = DashboardViewModel(
      accessRepository: _accessRepository,
      webSocketService: _webSocketService,
    );
    _staffViewModel = StaffViewModel(accessRepository: _accessRepository);
    _attendanceViewModel =
        AttendanceViewModel(accessRepository: _accessRepository);
    _devicesViewModel = DevicesViewModel(accessRepository: _accessRepository);

    _authViewModel.init();
  }

  @override
  void dispose() {
    _dashboardViewModel.dispose();
    _webSocketService.disconnect();
    _authViewModel.dispose();
    _staffViewModel.dispose();
    _attendanceViewModel.dispose();
    _devicesViewModel.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Burgood Access Control',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: ListenableBuilder(
        listenable: _authViewModel,
        builder: (context, _) {
          if (_authViewModel.isInitializing) {
            return const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            );
          }

          if (!_authViewModel.isAuthenticated) {
            return LoginView(viewModel: _authViewModel);
          }

          return HomeShellView(
            authViewModel: _authViewModel,
            dashboardViewModel: _dashboardViewModel,
            staffViewModel: _staffViewModel,
            attendanceViewModel: _attendanceViewModel,
            devicesViewModel: _devicesViewModel,
          );
        },
      ),
    );
  }
}
