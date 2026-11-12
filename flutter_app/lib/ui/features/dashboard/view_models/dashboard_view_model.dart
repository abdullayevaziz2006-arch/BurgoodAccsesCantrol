import 'dart:async';
import 'package:flutter/foundation.dart';
import '../../../../data/models/access_log.dart';
import '../../../../data/models/dashboard_stats.dart';
import '../../../../data/models/device_model.dart';
import '../../../../data/repositories/access_repository.dart';
import '../../../../data/services/websocket_service.dart';

class DashboardViewModel extends ChangeNotifier {
  DashboardViewModel({
    required AccessRepository accessRepository,
    required WebSocketService webSocketService,
  })  : _repo = accessRepository,
        _ws = webSocketService;

  final AccessRepository _repo;
  final WebSocketService _ws;
  StreamSubscription<AccessLog>? _wsSub;

  DashboardStats _stats = const DashboardStats();
  DashboardStats get stats => _stats;

  List<AccessLog> _liveLogs = [];
  List<AccessLog> get liveLogs => _liveLogs;

  List<DeviceModel> _devices = [];
  List<DeviceModel> get devices => _devices;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  void startLiveUpdates(String serverUrl) {
    _ws.connect(serverUrl);
    _wsSub?.cancel();
    _wsSub = _ws.events.listen((newLog) {
      _liveLogs = [newLog, ..._liveLogs.take(29)];
      refreshSilent();
      notifyListeners();
    });
  }

  Future<void> loadAll() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    try {
      final results = await Future.wait([
        _repo.getStats(),
        _repo.getLogs(limit: 25),
        _repo.getDevices(),
      ]);
      _stats = results[0] as DashboardStats;
      _liveLogs = results[1] as List<AccessLog>;
      _devices = results[2] as List<DeviceModel>;
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refreshSilent() async {
    try {
      _stats = await _repo.getStats();
      notifyListeners();
    } catch (_) {}
  }

  Future<String> openDoor(int deviceId) async {
    return _repo.openDoorRemote(deviceId);
  }

  @override
  void dispose() {
    _wsSub?.cancel();
    _ws.disconnect();
    super.dispose();
  }
}
