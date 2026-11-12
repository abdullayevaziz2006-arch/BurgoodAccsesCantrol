import 'dart:typed_data';
import '../models/access_log.dart';
import '../models/dashboard_stats.dart';
import '../models/device_model.dart';
import '../models/employee_user.dart';
import '../services/api_client.dart';

class AccessRepository {
  AccessRepository({required ApiClient apiClient}) : _api = apiClient;

  final ApiClient _api;

  Future<DashboardStats> getStats() async {
    final data = await _api.get('/attendance/stats');
    return DashboardStats.fromJson(data as Map<String, dynamic>);
  }

  Future<List<AccessLog>> getLogs({
    int limit = 100,
    String? search,
    String? direction,
    String? startDate,
    String? endDate,
    int? userId,
  }) async {
    final params = <String, String>{'limit': limit.toString()};
    if (search != null && search.trim().isNotEmpty) params['search'] = search.trim();
    if (direction != null && direction.isNotEmpty) params['direction'] = direction;
    if (startDate != null && startDate.isNotEmpty) params['start_date'] = startDate;
    if (endDate != null && endDate.isNotEmpty) params['end_date'] = endDate;
    if (userId != null) params['user_id'] = userId.toString();

    final data = await _api.get('/attendance/logs', queryParams: params);
    final list = (data as List?) ?? [];
    return list.map((e) => AccessLog.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<EmployeeUser>> getUsers({String? search, String? role}) async {
    final params = <String, String>{};
    if (search != null && search.trim().isNotEmpty) params['search'] = search.trim();
    if (role != null && role.isNotEmpty) params['role'] = role;

    final data = await _api.get('/users/', queryParams: params.isEmpty ? null : params);
    final list = (data as List?) ?? [];
    return list.map((e) => EmployeeUser.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<EmployeeUser> createUser({
    required String fullName,
    required String employeeNo,
    String role = 'staff',
    String? position,
    String? phoneNumber,
  }) async {
    final data = await _api.post('/users/', body: {
      'full_name': fullName.trim(),
      'employee_no': employeeNo.trim(),
      'role': role,
      if (position != null && position.trim().isNotEmpty) 'position': position.trim(),
      if (phoneNumber != null && phoneNumber.trim().isNotEmpty) 'phone_number': phoneNumber.trim(),
    });
    return EmployeeUser.fromJson(data as Map<String, dynamic>);
  }

  Future<void> uploadUserPhoto(int userId, Uint8List bytes, String filename) async {
    await _api.uploadPhotoBytes('/users/$userId/upload-photo', bytes, filename);
  }

  Future<void> syncUserToAll(int userId) async {
    await _api.post('/users/$userId/sync-to-all');
  }

  Future<List<DeviceModel>> getDevices() async {
    final data = await _api.get('/devices/');
    final list = (data as List?) ?? [];
    return list.map((e) => DeviceModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<String> openDoorRemote(int deviceId) async {
    final data = await _api.post('/devices/$deviceId/open-door') as Map<String, dynamic>;
    return data['message']?.toString() ?? 'Eshik ochildi';
  }

  Future<(bool, String)> testDevice(int deviceId) async {
    final data = await _api.post('/devices/$deviceId/test') as Map<String, dynamic>;
    return (data['success'] == true, data['message']?.toString() ?? 'Tekshirildi');
  }
}
