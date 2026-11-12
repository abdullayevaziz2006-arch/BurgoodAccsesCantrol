import 'package:flutter/foundation.dart';
import '../../../../data/models/device_model.dart';
import '../../../../data/repositories/access_repository.dart';

class DevicesViewModel extends ChangeNotifier {
  DevicesViewModel({required AccessRepository accessRepository}) : _repo = accessRepository;

  final AccessRepository _repo;

  List<DeviceModel> _devices = [];
  List<DeviceModel> get devices => _devices;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  Future<void> loadDevices() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    try {
      _devices = await _repo.getDevices();
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<String> openDoor(int deviceId) => _repo.openDoorRemote(deviceId);

  Future<(bool, String)> testConnection(int deviceId) => _repo.testDevice(deviceId);
}
