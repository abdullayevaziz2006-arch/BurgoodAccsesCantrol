import 'package:flutter/foundation.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../data/models/auth_models.dart';
import '../../../../data/repositories/auth_repository.dart';

class AuthViewModel extends ChangeNotifier {
  AuthViewModel({required AuthRepository authRepository}) : _authRepo = authRepository;

  final AuthRepository _authRepo;

  bool _isInitializing = true;
  bool get isInitializing => _isInitializing;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  AuthUser? _user;
  AuthUser? get user => _user;

  OrganizationInfo? _organization;
  OrganizationInfo? get organization => _organization;

  String _serverUrl = AppConstants.defaultServerUrl;
  String get serverUrl => _serverUrl;

  bool get isAuthenticated => _user != null;

  Future<void> init() async {
    _isInitializing = true;
    notifyListeners();
    try {
      final (restoredUser, restoredOrg, url) = await _authRepo.restoreSession();
      _user = restoredUser;
      _organization = restoredOrg;
      _serverUrl = url;
    } finally {
      _isInitializing = false;
      notifyListeners();
    }
  }

  Future<bool> login({
    required String username,
    required String password,
    required String serverUrl,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _authRepo.login(
        username: username,
        password: password,
        serverUrl: serverUrl,
      );
      _user = res.user;
      _organization = res.organization;
      _serverUrl = serverUrl.trim().replaceAll(RegExp(r'/+$'), '');
      return true;
    } catch (e) {
      _errorMessage = e.toString();
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _authRepo.logout();
    _user = null;
    _organization = null;
    notifyListeners();
  }
}
