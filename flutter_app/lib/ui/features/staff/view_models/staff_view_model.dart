import 'package:flutter/foundation.dart';
import '../../../../data/models/employee_user.dart';
import '../../../../data/repositories/access_repository.dart';

class StaffViewModel extends ChangeNotifier {
  StaffViewModel({required AccessRepository accessRepository}) : _repo = accessRepository;

  final AccessRepository _repo;

  List<EmployeeUser> _users = [];
  List<EmployeeUser> get users => _users;

  String _searchQuery = '';
  String get searchQuery => _searchQuery;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  bool _isSaving = false;
  bool get isSaving => _isSaving;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  List<EmployeeUser> get filteredUsers {
    if (_searchQuery.trim().isEmpty) return _users;
    final q = _searchQuery.trim().toLowerCase();
    return _users.where((u) {
      return u.fullName.toLowerCase().contains(q) ||
          u.employeeNo.toLowerCase().contains(q) ||
          (u.position?.toLowerCase().contains(q) ?? false);
    }).toList();
  }

  void setSearch(String query) {
    _searchQuery = query;
    notifyListeners();
  }

  Future<void> loadUsers() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    try {
      _users = await _repo.getUsers();
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> addStaffMember({
    required String fullName,
    required String employeeNo,
    String role = 'staff',
    String? position,
    String? phoneNumber,
    Uint8List? photoBytes,
    String? photoFilename,
    bool syncToTerminal = true,
  }) async {
    _isSaving = true;
    _errorMessage = null;
    notifyListeners();
    try {
      final created = await _repo.createUser(
        fullName: fullName,
        employeeNo: employeeNo,
        role: role,
        position: position,
        phoneNumber: phoneNumber,
      );
      if (photoBytes != null && photoFilename != null) {
        await _repo.uploadUserPhoto(created.id, photoBytes, photoFilename);
      }
      if (syncToTerminal) {
        try {
          await _repo.syncUserToAll(created.id);
        } catch (_) {}
      }
      await loadUsers();
      return true;
    } catch (e) {
      _errorMessage = e.toString();
      return false;
    } finally {
      _isSaving = false;
      notifyListeners();
    }
  }
}
